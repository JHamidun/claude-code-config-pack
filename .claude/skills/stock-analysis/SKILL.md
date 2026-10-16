---
name: stock-analysis
description: "Акции и компании через yfinance: цены, инсайдеры, рекомендации аналитиков, SEC. Триггеры: «акции», «биржа», «стоит ли покупать бумагу»."
type: actionable
---

# Stock Analysis

Comprehensive stock and company analysis using Python yfinance library.

## Dependencies

```bash
pip install yfinance pandas openpyxl
```

## Quick Start

```python
import yfinance as yf

# Company info
ticker = yf.Ticker("AAPL")
info = ticker.info  # Full profile
hist = ticker.history(period="1y")  # Price history
recs = ticker.recommendations  # Analyst recommendations
```

## Available Data via yfinance

| Что нужно | yfinance | CLI-подкоманда |
|-----------|----------|----------------|
| Профиль компании, сектор, сотрудники | `yf.Ticker(sym).info` | `profile` |
| Рейтинги аналитиков, таргеты | `yf.Ticker(sym).recommendations` | `recommendations` |
| OHLCV-история цен | `yf.Ticker(sym).history()` | `chart` |
| Сделки инсайдеров | `yf.Ticker(sym).insider_transactions` | `insiders` |
| История подач в SEC | `yf.Ticker(sym).sec_filings` | **нет — только из Python, см. ниже** |

> Раньше в левой колонке стояли имена инструментов Manus (`get_stock_profile` и т.д.) — след
> портирования. В этой среде их нет; искать «готовый тул» по этим именам бессмысленно.

**SEC — единственный пункт описания, до которого CLI не доводит.** `scripts/stock_analysis.py`
принимает только `profile, chart, recommendations, insiders, full, compare`; подкоманды `sec`
нет, и `full` её не включает. Берётся напрямую (проверено на yfinance 1.6.0 — AAPL отдал
79 записей):

```python
import yfinance as yf
for f in yf.Ticker("AAPL").sec_filings[:10]:
    print(f["date"], f["type"], f["title"], f["edgarUrl"])
```

## Script

Run analysis via: `python ~/.claude/skills/stock-analysis/scripts/stock_analysis.py`

```bash
# Company overview
python stock_analysis.py profile AAPL

# Price chart data
python stock_analysis.py chart AAPL --period 1y --interval 1d

# Analyst recommendations
python stock_analysis.py recommendations AAPL

# Insider transactions
python stock_analysis.py insiders AAPL

# Full analysis (all data)
python stock_analysis.py full AAPL

# Compare multiple stocks
python stock_analysis.py compare AAPL,MSFT,GOOGL --period 6mo

# Export to Excel
python stock_analysis.py full AAPL --excel output.xlsx
```

## Common Workflows

### Company Overview
```
User: "Tell me about AAPL"
-> profile (business summary, industry, employees)
-> recommendations (analyst outlook)
-> chart (recent performance)
```

### Investment Analysis
```
User: "Is TSLA a good buy?"
-> chart (price trends, 52-week range)
-> recommendations (analyst consensus, target price)
-> profile (business fundamentals)
-> insider_transactions (insider sentiment)
```

### Multi-Stock Comparison
```
User: "Compare AAPL vs MSFT vs GOOGL"
-> chart for each (relative performance)
-> profile for each (market cap, P/E, sector)
-> recommendations for each (ratings comparison)
-> Export side-by-side to Excel
```

## Key Data Points

### Profile: `ticker.info`
- `marketCap`, `sector`, `industry`, `fullTimeEmployees`
- `forwardPE`, `trailingPE`, `dividendYield`
- `fiftyTwoWeekHigh`, `fiftyTwoWeekLow`
- `targetMeanPrice`, `recommendationKey`

### History: `ticker.history(period, interval)`
- Periods: `1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max`
- Intervals: `1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo`
- Returns DataFrame with Open, High, Low, Close, Volume

### Recommendations: `ticker.recommendations`
- Columns: period, strongBuy, buy, hold, sell, strongSell

## When to Use

**Trigger words:** "stock", "share price", "AAPL", "TSLA", "$MSFT", "analyze company", "compare stocks", "insider trading", "SEC filing", "analyst rating", "акции", "курс", "биржа"

## Excel Export Integration

Use with skill `xlsx` for professional reports:

```python
import yfinance as yf
import pandas as pd

ticker = yf.Ticker("AAPL")
hist = ticker.history(period="1y")
hist.to_excel("aapl_history.xlsx", sheet_name="Price History")
```
