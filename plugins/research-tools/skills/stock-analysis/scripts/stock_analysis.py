"""
Stock Analysis - yfinance wrapper for comprehensive stock research.

Adapted from Manus AI Yahoo API proxy for Claude Code.
Uses yfinance library instead of internal API.

Usage:
    python stock_analysis.py profile AAPL
    python stock_analysis.py chart AAPL --period 1y --interval 1d
    python stock_analysis.py recommendations AAPL
    python stock_analysis.py insiders AAPL
    python stock_analysis.py full AAPL
    python stock_analysis.py compare AAPL,MSFT,GOOGL --period 6mo
    python stock_analysis.py full AAPL --excel output.xlsx

Dependencies:
    pip install yfinance pandas openpyxl
"""

import json
import sys
import argparse
from datetime import datetime

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print(json.dumps({"error": "Install dependencies: pip install yfinance pandas openpyxl"}))
    sys.exit(1)


def get_profile(symbol: str) -> dict:
    """Get company profile and key metrics."""
    ticker = yf.Ticker(symbol)
    info = ticker.info

    return {
        "symbol": symbol,
        "name": info.get("longName", ""),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "country": info.get("country", ""),
        "website": info.get("website", ""),
        "employees": info.get("fullTimeEmployees", 0),
        "summary": info.get("longBusinessSummary", ""),
        "market_cap": info.get("marketCap", 0),
        "currency": info.get("currency", "USD"),
        "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
        "previous_close": info.get("previousClose", 0),
        "52w_high": info.get("fiftyTwoWeekHigh", 0),
        "52w_low": info.get("fiftyTwoWeekLow", 0),
        "pe_ratio": info.get("trailingPE", 0),
        "forward_pe": info.get("forwardPE", 0),
        "dividend_yield": info.get("dividendYield", 0),
        "beta": info.get("beta", 0),
        "target_mean_price": info.get("targetMeanPrice", 0),
        "target_high": info.get("targetHighPrice", 0),
        "target_low": info.get("targetLowPrice", 0),
        "recommendation": info.get("recommendationKey", ""),
        "recommendation_mean": info.get("recommendationMean", 0),
    }


def get_chart(symbol: str, period: str = "1y", interval: str = "1d") -> dict:
    """Get price history as JSON."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)

    if hist.empty:
        return {"symbol": symbol, "error": "No data available", "data": []}

    records = []
    for date, row in hist.iterrows():
        records.append({
            "date": str(date.date()) if hasattr(date, 'date') else str(date),
            "open": round(row["Open"], 2),
            "high": round(row["High"], 2),
            "low": round(row["Low"], 2),
            "close": round(row["Close"], 2),
            "volume": int(row["Volume"]),
        })

    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "data_points": len(records),
        "start": records[0]["date"] if records else "",
        "end": records[-1]["date"] if records else "",
        "data": records,
    }


def get_recommendations(symbol: str) -> dict:
    """Get analyst recommendations."""
    ticker = yf.Ticker(symbol)

    result = {"symbol": symbol, "recommendations": [], "upgrades_downgrades": []}

    try:
        recs = ticker.recommendations
        if recs is not None and not recs.empty:
            for _, row in recs.tail(10).iterrows():
                result["recommendations"].append({
                    "period": str(row.get("period", "")),
                    "strongBuy": int(row.get("strongBuy", 0)),
                    "buy": int(row.get("buy", 0)),
                    "hold": int(row.get("hold", 0)),
                    "sell": int(row.get("sell", 0)),
                    "strongSell": int(row.get("strongSell", 0)),
                })
    except Exception:
        pass

    try:
        upgrades = ticker.upgrades_downgrades
        if upgrades is not None and not upgrades.empty:
            for date, row in upgrades.tail(10).iterrows():
                result["upgrades_downgrades"].append({
                    "date": str(date),
                    "firm": str(row.get("Firm", "")),
                    "to_grade": str(row.get("ToGrade", "")),
                    "from_grade": str(row.get("FromGrade", "")),
                    "action": str(row.get("Action", "")),
                })
    except Exception:
        pass

    return result


def get_insiders(symbol: str) -> dict:
    """Get insider transactions."""
    ticker = yf.Ticker(symbol)
    result = {"symbol": symbol, "transactions": [], "holders": []}

    try:
        insider = ticker.insider_transactions
        if insider is not None and not insider.empty:
            for _, row in insider.head(20).iterrows():
                result["transactions"].append({
                    "insider": str(row.get("Insider", "")),
                    "relation": str(row.get("Position", row.get("Relation", ""))),
                    "date": str(row.get("Start Date", row.get("Date", ""))),
                    "transaction": str(row.get("Transaction", "")),
                    "shares": int(row.get("Shares", 0)) if pd.notna(row.get("Shares", 0)) else 0,
                    "value": float(row.get("Value", 0)) if pd.notna(row.get("Value", 0)) else 0,
                })
    except Exception:
        pass

    try:
        holders = ticker.institutional_holders
        if holders is not None and not holders.empty:
            for _, row in holders.head(10).iterrows():
                result["holders"].append({
                    "holder": str(row.get("Holder", "")),
                    "shares": int(row.get("Shares", 0)) if pd.notna(row.get("Shares", 0)) else 0,
                    "date_reported": str(row.get("Date Reported", "")),
                    "pct_out": float(row.get("% Out", 0)) if pd.notna(row.get("% Out", 0)) else 0,
                    "value": float(row.get("Value", 0)) if pd.notna(row.get("Value", 0)) else 0,
                })
    except Exception:
        pass

    return result


def get_full_analysis(symbol: str) -> dict:
    """Get comprehensive analysis combining all data sources."""
    return {
        "symbol": symbol,
        "generated_at": datetime.now().isoformat(),
        "profile": get_profile(symbol),
        "chart": get_chart(symbol, period="6mo"),
        "recommendations": get_recommendations(symbol),
        "insiders": get_insiders(symbol),
    }


def compare_stocks(symbols: list, period: str = "6mo") -> dict:
    """Compare multiple stocks side by side."""
    results = {"symbols": symbols, "period": period, "comparison": []}

    for sym in symbols:
        profile = get_profile(sym)
        chart = get_chart(sym, period=period)
        results["comparison"].append({
            "symbol": sym,
            "name": profile.get("name", ""),
            "market_cap": profile.get("market_cap", 0),
            "current_price": profile.get("current_price", 0),
            "pe_ratio": profile.get("pe_ratio", 0),
            "52w_high": profile.get("52w_high", 0),
            "52w_low": profile.get("52w_low", 0),
            "recommendation": profile.get("recommendation", ""),
            "data_points": chart.get("data_points", 0),
        })

    return results


def export_to_excel(data: dict, output_path: str):
    """Export analysis data to Excel."""
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Profile sheet
        if "profile" in data:
            profile_df = pd.DataFrame([data["profile"]])
            profile_df.to_excel(writer, sheet_name="Profile", index=False)

        # Chart data sheet
        if "chart" in data and data["chart"].get("data"):
            chart_df = pd.DataFrame(data["chart"]["data"])
            chart_df.to_excel(writer, sheet_name="Price History", index=False)

        # Recommendations sheet
        if "recommendations" in data:
            recs = data["recommendations"].get("recommendations", [])
            if recs:
                recs_df = pd.DataFrame(recs)
                recs_df.to_excel(writer, sheet_name="Recommendations", index=False)

        # Insiders sheet
        if "insiders" in data:
            txns = data["insiders"].get("transactions", [])
            if txns:
                txns_df = pd.DataFrame(txns)
                txns_df.to_excel(writer, sheet_name="Insider Transactions", index=False)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Stock Analysis Tool")
    parser.add_argument("command", choices=["profile", "chart", "recommendations", "insiders", "full", "compare"])
    parser.add_argument("symbol", help="Stock symbol(s), comma-separated for compare")
    parser.add_argument("--period", default="1y", help="Chart period (1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max)")
    parser.add_argument("--interval", default="1d", help="Chart interval (1m,5m,15m,30m,1h,1d,1wk,1mo)")
    parser.add_argument("--excel", help="Export to Excel file path")

    args = parser.parse_args()

    try:
        if args.command == "profile":
            result = get_profile(args.symbol)
        elif args.command == "chart":
            result = get_chart(args.symbol, args.period, args.interval)
        elif args.command == "recommendations":
            result = get_recommendations(args.symbol)
        elif args.command == "insiders":
            result = get_insiders(args.symbol)
        elif args.command == "full":
            result = get_full_analysis(args.symbol)
        elif args.command == "compare":
            symbols = [s.strip() for s in args.symbol.split(",")]
            result = compare_stocks(symbols, args.period)
        else:
            result = {"error": f"Unknown command: {args.command}"}

        if args.excel and args.command in ("full", "compare"):
            export_to_excel(result, args.excel)
            result["excel_exported"] = args.excel

        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
