"""
Main entry point - Stock Sentiment Analysis System
"""
import argparse
import json
import os
from datetime import datetime
from typing import List, Dict
import pandas as pd

from news_fetcher import NewsFetcher
from sentiment_analyzer import SentimentAnalyzer
import config

# Results directory
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def ensure_results_dir():
    """Create results directory if it doesn't exist"""
    os.makedirs(RESULTS_DIR, exist_ok=True)


class StockSentimentSystem:
    """Stock Sentiment Analysis System"""

    def __init__(self):
        self.news_fetcher = NewsFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()

    def analyze_stock(self, ticker: str, news_limit: int = 20) -> Dict:
        """
        Analyze sentiment for a single stock.

        Args:
            ticker: Stock ticker symbol
            news_limit: Number of news articles to fetch

        Returns:
            Complete analysis result
        """
        print(f"\n{'='*60}")
        print(f"Analyzing: {ticker}")
        print(f"{'='*60}")

        # 1. Fetch news
        print(f"\n[1/2] Fetching news (last {config.NEWS_LOOKBACK_DAYS} days, limit {news_limit})...")
        news_list = self.news_fetcher.get_news(ticker, limit=news_limit)

        if not news_list:
            print(f"Warning: No news found for {ticker}")
            return {
                "ticker": ticker,
                "analysis_time": datetime.now().isoformat(),
                "final_score": 50,
                "sentiment": "neutral",
                "news_count": 0,
                "message": "No news found"
            }

        print(f"  Found {len(news_list)} articles")

        # 2. Analyze sentiment
        print(f"\n[2/2] Analyzing sentiment...")
        analysis_results = self.sentiment_analyzer.analyze_news_batch(news_list)

        # 3. Aggregate results
        aggregated = self.sentiment_analyzer.aggregate_sentiment(analysis_results)

        result = {
            "ticker": ticker,
            "analysis_time": datetime.now().isoformat(),
            "lookback_days": config.NEWS_LOOKBACK_DAYS,
            **aggregated
        }

        return result

    def analyze_multiple_stocks(
        self,
        tickers: List[str] = None,
        news_limit: int = 20
    ) -> pd.DataFrame:
        """
        Analyze multiple stocks.

        Args:
            tickers: List of tickers, defaults to config.TECH_STOCKS
            news_limit: Number of news articles per stock

        Returns:
            DataFrame with all analysis results
        """
        tickers = tickers or config.TECH_STOCKS
        all_results = []
        rows = []

        for ticker in tickers:
            result = self.analyze_stock(ticker, news_limit)
            all_results.append(result)
            rows.append({
                "ticker": result["ticker"],
                "score": result["final_score"],
                "sentiment": result["sentiment"],
                "news_count": result["news_count"],
                "avg_confidence": result.get("avg_confidence", 0),
                "bullish": result.get("bullish_count", 0),
                "bearish": result.get("bearish_count", 0),
                "neutral": result.get("neutral_count", 0),
            })

        df = pd.DataFrame(rows)
        df = df.sort_values("score", ascending=False).reset_index(drop=True)

        # Save results
        self.save_results(all_results, df)

        return df

    def save_results(self, full_results: List[Dict], summary_df: pd.DataFrame):
        """
        Save analysis results to files.

        Args:
            full_results: List of detailed result dicts (one per stock)
            summary_df: Summary DataFrame
        """
        ensure_results_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save detailed JSON
        json_path = os.path.join(RESULTS_DIR, f"analysis_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(full_results, f, indent=2, ensure_ascii=False)

        # Save summary CSV
        csv_path = os.path.join(RESULTS_DIR, f"summary_{timestamp}.csv")
        summary_df.to_csv(csv_path, index=False)

        print(f"\n[Saved] Detailed results -> {json_path}")
        print(f"[Saved] Summary CSV     -> {csv_path}")

    def save_single_result(self, result: Dict):
        """Save a single stock analysis result"""
        ensure_results_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ticker = result.get("ticker", "UNKNOWN")

        json_path = os.path.join(RESULTS_DIR, f"{ticker}_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n[Saved] {ticker} result -> {json_path}")

    def print_result(self, result: Dict):
        """Print analysis result for a single stock"""
        print(f"\n{'='*60}")
        print(f"Result: {result['ticker']}")
        print(f"{'='*60}")
        print(f"Final Score:    {result['final_score']:.1f} / 100")
        print(f"Sentiment:      {result['sentiment'].upper()}")
        print(f"Articles:       {result['news_count']}")
        print(f"Lookback:       {result.get('lookback_days', 'N/A')} days")
        print(f"Avg Confidence: {result.get('avg_confidence', 0):.1f}%")
        print(f"Bullish/Neutral/Bearish: {result.get('bullish_count', 0)}/{result.get('neutral_count', 0)}/{result.get('bearish_count', 0)}")

        if "details" in result and result["details"]:
            print(f"\n--- Article Details ---")
            for i, detail in enumerate(result["details"], 1):
                sentiment_tag = {
                    "bullish": "[+]",
                    "neutral": "[=]",
                    "bearish": "[-]"
                }.get(detail.get("sentiment", "neutral"), "[?]")

                title = detail.get('title', 'N/A')[:60]
                print(f"\n{i}. {sentiment_tag} [Score:{detail.get('score', 50)}] {title}")
                print(f"   Source: {detail.get('source', 'N/A')} | {detail.get('published_utc', 'N/A')[:10]}")
                print(f"   Reason: {detail.get('reason', 'N/A')}")

    def print_summary(self, df: pd.DataFrame):
        """Print summary table for multiple stocks"""
        print(f"\n{'='*70}")
        print("Stock Sentiment Analysis Summary")
        print(f"{'='*70}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Lookback: {config.NEWS_LOOKBACK_DAYS} days")
        print(f"Stocks Analyzed: {len(df)}")
        print(f"\n{'='*70}")

        print(f"{'Rank':<6} {'Ticker':<8} {'Score':<8} {'Sentiment':<12} {'Articles':<10} {'Confidence':<10}")
        print("-" * 70)

        for i, row in df.iterrows():
            sentiment_display = {
                "bullish": "BULLISH",
                "neutral": "NEUTRAL",
                "bearish": "BEARISH"
            }.get(row["sentiment"], "UNKNOWN")

            print(f"{i+1:<6} {row['ticker']:<8} {row['score']:<8.1f} {sentiment_display:<12} {row['news_count']:<10} {row['avg_confidence']:<10.1f}")

        print("-" * 70)

        bullish_stocks = df[df["sentiment"] == "bullish"]["ticker"].tolist()
        bearish_stocks = df[df["sentiment"] == "bearish"]["ticker"].tolist()

        if bullish_stocks:
            print(f"\nBullish: {', '.join(bullish_stocks)}")
        if bearish_stocks:
            print(f"Bearish: {', '.join(bearish_stocks)}")

        print(f"\nAverage Score: {df['score'].mean():.1f}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Stock Sentiment Analysis System")
    parser.add_argument(
        "-t", "--ticker",
        type=str,
        help="Analyze a single stock (e.g., AAPL)"
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Analyze all configured tech stocks"
    )
    parser.add_argument(
        "-n", "--news-limit",
        type=int,
        default=20,
        help="Number of news articles per stock (default: 20)"
    )

    args = parser.parse_args()

    system = StockSentimentSystem()

    if args.ticker:
        result = system.analyze_stock(args.ticker.upper(), args.news_limit)
        system.print_result(result)
        system.save_single_result(result)

    elif args.all:
        df = system.analyze_multiple_stocks(news_limit=args.news_limit)
        system.print_summary(df)

    else:
        print("=" * 60)
        print("Stock Sentiment Analysis System")
        print("=" * 60)
        print("\nUsage:")
        print("  python main.py -t AAPL          # Analyze single stock")
        print("  python main.py -a               # Analyze all tech stocks")
        print("  python main.py -t NVDA -n 10    # Analyze NVDA with 10 articles")
        print("\nRunning demo with AAPL, NVDA, MSFT...")

        demo_stocks = ["AAPL", "NVDA", "MSFT"]
        df = system.analyze_multiple_stocks(tickers=demo_stocks, news_limit=20)
        system.print_summary(df)


if __name__ == "__main__":
    main()
