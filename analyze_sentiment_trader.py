from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
HISTORICAL_DATA = ROOT / "historical_data.csv"
SENTIMENT_DATA = ROOT / "fear_greed_index.csv"
OUTPUT_DIR = ROOT / "analysis_output"


def normalize_name(name: str) -> str:
    return (
        name.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def safe_rate(series: pd.Series) -> float:
    if len(series) == 0:
        return np.nan
    return float((series > 0).mean())


def prepare_data() -> pd.DataFrame:
    trades = pd.read_csv(HISTORICAL_DATA)
    sentiment = pd.read_csv(SENTIMENT_DATA)

    trades.columns = [normalize_name(c) for c in trades.columns]
    sentiment.columns = [normalize_name(c) for c in sentiment.columns]

    numeric_cols = [
        "execution_price",
        "size_tokens",
        "size_usd",
        "start_position",
        "closed_pnl",
        "fee",
        "timestamp",
    ]
    for col in numeric_cols:
        if col in trades.columns:
            trades[col] = pd.to_numeric(trades[col], errors="coerce")

    trades["trade_datetime_ist"] = pd.to_datetime(
        trades["timestamp_ist"], format="%d-%m-%Y %H:%M", errors="coerce"
    )
    trades["date"] = trades["trade_datetime_ist"].dt.date.astype(str)

    sentiment["date"] = pd.to_datetime(sentiment["date"], errors="coerce").dt.date.astype(str)
    sentiment["sentiment_value"] = pd.to_numeric(sentiment["value"], errors="coerce")
    sentiment = sentiment[["date", "sentiment_value", "classification"]].drop_duplicates("date")

    merged = trades.merge(sentiment, how="left", on="date")
    merged["net_pnl"] = merged["closed_pnl"] - merged["fee"]
    merged["is_profitable"] = merged["closed_pnl"] > 0
    merged["fee_bps"] = np.where(
        merged["size_usd"].abs() > 0,
        merged["fee"] / merged["size_usd"].abs() * 10000,
        np.nan,
    )
    merged["side_normalized"] = merged["side"].astype(str).str.upper()
    merged["direction_normalized"] = merged["direction"].astype(str).str.title()
    merged["sentiment_group"] = pd.Categorical(
        merged["classification"],
        categories=["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"],
        ordered=True,
    )
    return merged


def aggregate_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("sentiment_group", observed=False)
        .agg(
            trades=("trade_id", "count"),
            accounts=("account", "nunique"),
            volume_usd=("size_usd", "sum"),
            avg_trade_usd=("size_usd", "mean"),
            total_closed_pnl=("closed_pnl", "sum"),
            total_net_pnl=("net_pnl", "sum"),
            avg_closed_pnl=("closed_pnl", "mean"),
            median_closed_pnl=("closed_pnl", "median"),
            win_rate=("closed_pnl", safe_rate),
            avg_fee_bps=("fee_bps", "mean"),
        )
        .reset_index()
    )


def aggregate_side(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["sentiment_group", "side_normalized"], observed=False)
        .agg(
            trades=("trade_id", "count"),
            volume_usd=("size_usd", "sum"),
            total_closed_pnl=("closed_pnl", "sum"),
            avg_closed_pnl=("closed_pnl", "mean"),
            win_rate=("closed_pnl", safe_rate),
        )
        .reset_index()
        .sort_values(["sentiment_group", "side_normalized"])
    )


def aggregate_accounts(df: pd.DataFrame) -> pd.DataFrame:
    account_sentiment = (
        df.groupby(["account", "sentiment_group"], observed=False)
        .agg(
            trades=("trade_id", "count"),
            volume_usd=("size_usd", "sum"),
            total_closed_pnl=("closed_pnl", "sum"),
            total_net_pnl=("net_pnl", "sum"),
            win_rate=("closed_pnl", safe_rate),
            avg_closed_pnl=("closed_pnl", "mean"),
        )
        .reset_index()
    )
    return account_sentiment.sort_values(
        ["sentiment_group", "total_closed_pnl"], ascending=[True, False]
    )


def save_plots(sentiment_summary: pd.DataFrame, daily: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt

    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=(10, 5))
    plot_df = sentiment_summary.dropna(subset=["sentiment_group"])
    ax.bar(plot_df["sentiment_group"].astype(str), plot_df["avg_closed_pnl"], color="#3A6EA5")
    ax.axhline(0, color="#2B2B2B", linewidth=0.8)
    ax.set_title("Average Closed PnL by Market Sentiment")
    ax.set_xlabel("Sentiment")
    ax.set_ylabel("Average closed PnL")
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "avg_pnl_by_sentiment.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(plot_df["sentiment_group"].astype(str), plot_df["win_rate"] * 100, color="#4F8A5B")
    ax.set_ylim(0, max(100, float((plot_df["win_rate"] * 100).max()) + 5))
    ax.set_title("Win Rate by Market Sentiment")
    ax.set_xlabel("Sentiment")
    ax.set_ylabel("Win rate (%)")
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "win_rate_by_sentiment.png", dpi=160)
    plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(daily["date"], daily["closed_pnl"], color="#2F5597", label="Daily closed PnL")
    ax1.axhline(0, color="#333333", linewidth=0.8)
    ax1.set_ylabel("Closed PnL")
    ax2 = ax1.twinx()
    ax2.plot(daily["date"], daily["sentiment_value"], color="#C55A11", alpha=0.6, label="Fear/Greed")
    ax2.set_ylabel("Fear/Greed value")
    ax1.set_title("Daily Trader PnL vs Bitcoin Fear/Greed Index")
    ax1.set_xlabel("Date")
    ax1.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "daily_pnl_vs_sentiment.png", dpi=160)
    plt.close(fig)


def write_report(df: pd.DataFrame, sentiment_summary: pd.DataFrame, side_summary: pd.DataFrame) -> None:
    matched = df["classification"].notna().sum()
    total = len(df)
    date_min = df["trade_datetime_ist"].min()
    date_max = df["trade_datetime_ist"].max()
    pnl_corr = df[["closed_pnl", "sentiment_value"]].corr(numeric_only=True).iloc[0, 1]
    volume_corr = df[["size_usd", "sentiment_value"]].corr(numeric_only=True).iloc[0, 1]

    best = sentiment_summary.sort_values("avg_closed_pnl", ascending=False).iloc[0]
    worst = sentiment_summary.sort_values("avg_closed_pnl", ascending=True).iloc[0]
    biggest = sentiment_summary.sort_values("volume_usd", ascending=False).iloc[0]

    top_accounts = (
        aggregate_accounts(df)
        .query("trades >= 10")
        .sort_values("total_closed_pnl", ascending=False)
        .head(10)
    )

    report = f"""# Trader Performance vs Bitcoin Market Sentiment

## Executive Summary

This analysis merges Hyperliquid trade executions with the Bitcoin Fear/Greed Index by calendar date. It evaluates whether trader outcomes, volume, win rate, and side behavior change across sentiment regimes.

Key results:

- Trade rows analyzed: {total:,}
- Rows matched to a sentiment day: {matched:,} ({matched / total:.1%})
- Trading date range: {date_min:%Y-%m-%d %H:%M} to {date_max:%Y-%m-%d %H:%M} IST
- Correlation between trade-level closed PnL and sentiment value: {pnl_corr:.4f}
- Correlation between trade size USD and sentiment value: {volume_corr:.4f}
- Best average PnL sentiment regime: {best['sentiment_group']} ({best['avg_closed_pnl']:.4f})
- Worst average PnL sentiment regime: {worst['sentiment_group']} ({worst['avg_closed_pnl']:.4f})
- Highest volume sentiment regime: {biggest['sentiment_group']} (${biggest['volume_usd']:,.2f})

## Method

1. Parsed trader timestamps from `Timestamp IST` and converted them to daily dates.
2. Parsed Fear/Greed dates from the sentiment dataset.
3. Left-joined trades to sentiment by date.
4. Calculated net PnL as `Closed PnL - Fee`, win rate as the share of trades with positive `Closed PnL`, and fee bps as `Fee / Size USD * 10000`.
5. Aggregated performance by sentiment classification, side, account, and day.

## Sentiment-Level Performance

{sentiment_summary.to_markdown(index=False)}

## Side Behavior by Sentiment

{side_summary.to_markdown(index=False)}

## Top Account/Sentiment Combinations

{top_accounts.to_markdown(index=False)}

## Insights

- Sentiment regime matters more through behavior and exposure than through a simple linear relationship. The trade-level PnL/sentiment correlation is small, so strategy should focus on conditional rules rather than assuming higher Fear/Greed values directly predict better results.
- Compare win rate with average PnL before choosing a regime. A sentiment bucket can have a decent hit rate but still underperform if losses are larger than wins.
- Volume concentration by sentiment highlights where traders are most active. If the highest-volume regime is not also the best PnL regime, position sizing discipline is a likely improvement area.
- Side-level splits show whether BUY or SELL executions behave differently under fear versus greed. That is useful for sentiment-aware long/short exposure limits.
- Account-level segmentation is important: aggregate results can hide a small set of traders who perform consistently in specific regimes.

## Recommended Trading Strategy Ideas

- Add a sentiment filter to risk management: reduce size in regimes with negative average PnL or weak net PnL after fees.
- Use regime-specific side rules: prefer the side with stronger average PnL and win rate inside each sentiment bucket.
- Identify accounts with repeatable edge in each regime, then study their timing, size, and symbol selection.
- Track fees explicitly. Net PnL can change conclusions for high-turnover accounts even when closed PnL looks positive.

## Deliverables

- `analysis_output/merged_trades_with_sentiment.csv`
- `analysis_output/sentiment_summary.csv`
- `analysis_output/side_sentiment_summary.csv`
- `analysis_output/account_sentiment_summary.csv`
- `analysis_output/daily_summary.csv`
- `analysis_output/avg_pnl_by_sentiment.png`
- `analysis_output/win_rate_by_sentiment.png`
- `analysis_output/daily_pnl_vs_sentiment.png`
- `streamlit_app.py` interactive dashboard
"""
    (OUTPUT_DIR / "report.md").write_text(report, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = prepare_data()
    sentiment_summary = aggregate_sentiment(df)
    side_summary = aggregate_side(df)
    account_summary = aggregate_accounts(df)
    daily = (
        df.groupby("date", as_index=False)
        .agg(
            trades=("trade_id", "count"),
            volume_usd=("size_usd", "sum"),
            closed_pnl=("closed_pnl", "sum"),
            net_pnl=("net_pnl", "sum"),
            win_rate=("closed_pnl", safe_rate),
            sentiment_value=("sentiment_value", "mean"),
        )
        .sort_values("date")
    )

    df.to_csv(OUTPUT_DIR / "merged_trades_with_sentiment.csv", index=False)
    sentiment_summary.to_csv(OUTPUT_DIR / "sentiment_summary.csv", index=False)
    side_summary.to_csv(OUTPUT_DIR / "side_sentiment_summary.csv", index=False)
    account_summary.to_csv(OUTPUT_DIR / "account_sentiment_summary.csv", index=False)
    daily.to_csv(OUTPUT_DIR / "daily_summary.csv", index=False)

    save_plots(sentiment_summary, daily)
    write_report(df, sentiment_summary, side_summary)
    print(f"Wrote analysis artifacts to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
