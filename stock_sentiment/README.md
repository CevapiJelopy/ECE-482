# LLM-Based Stock Sentiment Analysis

**ECE 482 Senior Design Project** — University of Miami

A web-based stock analysis tool that uses LLM API to evaluate financial news sentiment for technology sector stocks and generate a quantitative 0–100 bullishness score.

## Project Structure

```
stock_sentiment/
├── config.py              # Configuration (API keys, stock list, prompt, params)
├── news_fetcher.py        # Polygon.io news retrieval module
├── sentiment_analyzer.py  # LLM sentiment analysis (WaveSpeed AI / Claude 3.7)
├── main.py                # Main entry point (CLI)
├── requirements.txt       # Python dependencies
├── .env                   # API keys (DO NOT commit)
├── .env.example           # API key template
└── results/               # Auto-saved analysis results (JSON + CSV)
```

## Prerequisites

- Python 3.10+
- [Polygon.io](https://polygon.io/) API key (free tier works)
- [WaveSpeed AI](https://wavespeed.ai/) API key

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/cccccclu26/ECE-482.git
cd ECE-482/stock_sentiment
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Copy the example file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
POLYGON_API_KEY=your_polygon_api_key_here
WAVESPEED_API_KEY=your_wavespeed_api_key_here
```

## Usage

All commands should be run from the `stock_sentiment/` directory.

### Analyze a single stock

```bash
python main.py -t AAPL
```

### Analyze a single stock with custom article count

```bash
python main.py -t NVDA -n 10
```

### Analyze all configured tech stocks

```bash
python main.py -a
```

### Run demo mode (AAPL, NVDA, MSFT)

```bash
python main.py
```

### Command-line options

| Flag | Description | Default |
|------|-------------|---------|
| `-t TICKER` | Analyze a single stock by ticker symbol | — |
| `-a` | Analyze all 10 configured tech stocks | — |
| `-n NUM` | Number of news articles to fetch per stock | 20 |
| *(no flags)* | Run demo mode with 3 stocks | — |

## Configuration

Key parameters in `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DEFAULT_NEWS_LIMIT` | 20 | Articles fetched per stock |
| `NEWS_LOOKBACK_DAYS` | 7 | How many days back to search for news |
| `MAX_CONCURRENT_LLM_CALLS` | 5 | Parallel LLM API workers |
| `LLM_MODEL` | `anthropic/claude-3.7-sonnet` | LLM model used for analysis |

### Default stock list

AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, AMD, INTC, CRM

To modify, edit the `TECH_STOCKS` list in `config.py`.

## Output

### Terminal output

Each analysis prints:
- Final sentiment score (0–100)
- Overall sentiment label (BULLISH / NEUTRAL / BEARISH)
- Article count and average confidence
- Per-article breakdown with score, source, date, and reasoning

### Saved results

Results are automatically saved to the `results/` directory:

- **Single stock**: `results/{TICKER}_{timestamp}.json`
- **Batch analysis**: `results/analysis_{timestamp}.json` + `results/summary_{timestamp}.csv`

Example JSON structure:

```json
{
  "ticker": "AAPL",
  "analysis_time": "2026-02-06T16:06:59",
  "lookback_days": 7,
  "final_score": 51.65,
  "sentiment": "neutral",
  "news_count": 20,
  "avg_confidence": 68.25,
  "bullish_count": 5,
  "bearish_count": 4,
  "neutral_count": 11,
  "details": [
    {
      "sentiment": "neutral",
      "score": 50,
      "confidence": 60,
      "reason": "...",
      "title": "...",
      "source": "The Motley Fool",
      "published_utc": "2026-02-06T17:07:00Z"
    }
  ]
}
```

## How It Works

1. **News Fetching** — Retrieves recent news articles from Polygon.io for the given ticker (default: last 7 days)
2. **LLM Sentiment Analysis** — Sends each article to Claude 3.7 Sonnet via WaveSpeed AI API with a structured prompt; receives a JSON response with sentiment label, score (0–100), confidence, and reasoning
3. **Aggregation** — Computes a confidence-weighted average of all article scores to produce a final stock-level sentiment score
4. **Output & Save** — Prints results to terminal and auto-saves to `results/` directory

## Important Notes

- **Never commit `.env`** — it contains your API keys
- API calls cost money — monitor your usage on Polygon.io and WaveSpeed AI dashboards
- This is an **educational project**, not professional financial advice
- Past performance does not guarantee future results

## Team

- Zonglu Chen — LLM Pipeline & Evaluation
- Jorge Garzon — Backend & Data Infrastructure
- Alexander Pena — Web Interface & User Experience
- Advisor: Dr. Mingzhe Chen

## License

This project is for educational purposes as part of ECE 481/482 Senior Design at the University of Miami.
