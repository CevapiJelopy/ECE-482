"""
Sentiment Analysis Module - Uses WaveSpeed AI API (Claude 3.7 Sonnet) for news sentiment
Supports concurrent LLM calls for faster batch analysis.
"""
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import config


class SentimentAnalyzer:
    """Analyze news sentiment using LLM via WaveSpeed AI API"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.WAVESPEED_API_KEY

        if not self.api_key:
            raise ValueError("WaveSpeed API key is required. Please set WAVESPEED_API_KEY in .env file.")

        self.api_url = config.WAVESPEED_API_URL
        self.model = config.LLM_MODEL
        self.max_workers = config.MAX_CONCURRENT_LLM_CALLS

    def _call_llm(self, prompt: str) -> str:
        """
        Call WaveSpeed AI API and return the response text.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Response text from the LLM
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "enable_sync_mode": True,
            "model": self.model,
            "priority": "latency",
            "prompt": prompt,
            "reasoning": False
        }

        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()

        # Extract text from WaveSpeed response
        if data.get("code") == 200 and data.get("data", {}).get("outputs"):
            return data["data"]["outputs"][0]

        raise RuntimeError(f"LLM API error: {data.get('message', 'Unknown error')}")

    def analyze_single_news(self, news: Dict, index: int = 0, total: int = 0) -> Dict:
        """
        Analyze sentiment for a single news article.

        Args:
            news: News dict with ticker, title, description, published_utc
            index: Current article index (for logging)
            total: Total number of articles (for logging)

        Returns:
            Sentiment result with sentiment, score, confidence, reason
        """
        prompt = config.SENTIMENT_PROMPT.format(
            ticker=news.get("ticker", "Unknown"),
            title=news.get("title", ""),
            description=news.get("description", ""),
            published_date=news.get("published_utc", "")
        )

        try:
            result_text = self._call_llm(prompt)

            # Clean up potential markdown code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)

            # Attach original news info
            result["title"] = news.get("title", "")
            result["source"] = news.get("source", "")
            result["published_utc"] = news.get("published_utc", "")

            if index and total:
                print(f"  [{index}/{total}] Done - {result.get('sentiment', '?')} ({result.get('score', '?')})")

            return result

        except json.JSONDecodeError as e:
            print(f"  [{index}/{total}] JSON parse failed: {e}")
            return self._default_result(news)

        except Exception as e:
            print(f"  [{index}/{total}] Analysis failed: {e}")
            return self._default_result(news)

    def _default_result(self, news: Dict) -> Dict:
        """Return a default neutral result on failure"""
        return {
            "sentiment": "neutral",
            "score": 50,
            "confidence": 0,
            "reason": "Analysis failed, using default",
            "title": news.get("title", ""),
            "source": news.get("source", ""),
            "published_utc": news.get("published_utc", "")
        }

    def analyze_news_batch(self, news_list: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for a batch of news articles using concurrent LLM calls.

        Args:
            news_list: List of news dicts

        Returns:
            List of sentiment results (in original order)
        """
        total = len(news_list)
        print(f"  Launching {total} analyses with {self.max_workers} concurrent workers...")

        results = [None] * total

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(
                    self.analyze_single_news, news, i + 1, total
                ): i
                for i, news in enumerate(news_list)
            }

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    print(f"  [{idx+1}/{total}] Worker error: {e}")
                    results[idx] = self._default_result(news_list[idx])

        return results

    def aggregate_sentiment(self, results: List[Dict]) -> Dict:
        """
        Aggregate sentiment scores from multiple articles into a stock-level score.

        Uses confidence-weighted average.

        Args:
            results: List of sentiment results

        Returns:
            Aggregated sentiment with final_score, sentiment, counts, etc.
        """
        if not results:
            return {
                "final_score": 50,
                "sentiment": "neutral",
                "news_count": 0,
                "avg_confidence": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0
            }

        # Count sentiment categories
        bullish_count = sum(1 for r in results if r.get("sentiment") == "bullish")
        bearish_count = sum(1 for r in results if r.get("sentiment") == "bearish")
        neutral_count = sum(1 for r in results if r.get("sentiment") == "neutral")

        # Confidence-weighted average
        total_weight = 0
        weighted_score = 0

        for r in results:
            confidence = r.get("confidence", 50)
            score = r.get("score", 50)

            weight = confidence / 100.0 if confidence > 0 else 0.5
            weighted_score += score * weight
            total_weight += weight

        if total_weight > 0:
            final_score = weighted_score / total_weight
        else:
            final_score = 50

        # Determine overall sentiment
        if final_score >= 60:
            overall_sentiment = "bullish"
        elif final_score <= 40:
            overall_sentiment = "bearish"
        else:
            overall_sentiment = "neutral"

        avg_confidence = sum(r.get("confidence", 50) for r in results) / len(results)

        return {
            "final_score": round(final_score, 2),
            "sentiment": overall_sentiment,
            "news_count": len(results),
            "avg_confidence": round(avg_confidence, 2),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "details": results
        }


# Test code
if __name__ == "__main__":
    test_news = [
        {
            "ticker": "AAPL",
            "title": "Apple Reports Record iPhone Sales in Q4",
            "description": "Apple Inc. announced record-breaking iPhone sales for the fourth quarter, exceeding analyst expectations by 15%.",
            "published_utc": "2026-02-05T10:00:00Z",
            "source": "Reuters"
        },
        {
            "ticker": "AAPL",
            "title": "Apple Faces Supply Chain Challenges in China",
            "description": "Apple is experiencing production delays at its major manufacturing facilities in China.",
            "published_utc": "2026-02-04T08:00:00Z",
            "source": "Bloomberg"
        }
    ]

    analyzer = SentimentAnalyzer()

    print("=" * 50)
    print("Testing Sentiment Analysis (Concurrent)")
    print("=" * 50)

    results = analyzer.analyze_news_batch(test_news)

    for r in results:
        print(f"\nTitle: {r['title']}")
        print(f"Sentiment: {r['sentiment']} | Score: {r['score']} | Confidence: {r['confidence']}")
        print(f"Reason: {r['reason']}")

    aggregated = analyzer.aggregate_sentiment(results)
    print(f"\nFinal Score: {aggregated['final_score']}")
    print(f"Overall: {aggregated['sentiment']}")
