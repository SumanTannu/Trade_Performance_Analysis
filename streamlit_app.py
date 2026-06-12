from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "analysis_output"
MERGED_DATA = OUTPUT_DIR / "merged_trades_with_sentiment.csv"

SENTIMENT_ORDER = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]


st.set_page_config(
    page_title="Trader Sentiment Tracker",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if not MERGED_DATA.exists():
        st.error(
            "Missing analysis_output/merged_trades_with_sentiment.csv. "
            "Run `python analyze_sentiment_trader.py` first."
        )
        st.stop()

    df = pd.read_csv(MERGED_DATA)
    df["trade_datetime_ist"] = pd.to_datetime(df["trade_datetime_ist"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["hour"] = df["trade_datetime_ist"].dt.hour
    df["weekday"] = df["trade_datetime_ist"].dt.day_name()
    df["sentiment_group"] = pd.Categorical(
        df["classification"], categories=SENTIMENT_ORDER, ordered=True
    )
    return df


def safe_rate(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    return float((series > 0).mean())


def currency(value: float) -> str:
    return f"${value:,.2f}"


def number(value: float) -> str:
    return f"{value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def summarize(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    return (
        df.groupby(group_cols, observed=False)
        .agg(
            trades=("trade_id", "count"),
            accounts=("account", "nunique"),
            volume_usd=("size_usd", "sum"),
            closed_pnl=("closed_pnl", "sum"),
            net_pnl=("net_pnl", "sum"),
            avg_pnl=("closed_pnl", "mean"),
            median_pnl=("closed_pnl", "median"),
            win_rate=("closed_pnl", safe_rate),
            avg_fee_bps=("fee_bps", "mean"),
        )
        .reset_index()
    )


def bar_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = ""):
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
        .encode(
            x=alt.X(x, sort=SENTIMENT_ORDER if x.startswith("sentiment") else "-y"),
            y=alt.Y(y),
            tooltip=list(df.columns),
        )
        .properties(title=title, height=330)
    )
    if color:
        chart = chart.encode(color=alt.Color(color))
    return chart


df = load_data()

st.title("Trader Sentiment Tracker")
st.caption("Interactive exploration of Hyperliquid trader performance versus Bitcoin Fear/Greed regimes.")

with st.sidebar:
    st.header("Filters")
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    selected_dates = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    sentiments = st.multiselect(
        "Sentiment",
        SENTIMENT_ORDER,
        default=SENTIMENT_ORDER,
    )
    sides = st.multiselect(
        "Side",
        sorted(df["side_normalized"].dropna().unique()),
        default=sorted(df["side_normalized"].dropna().unique()),
    )
    coins = st.multiselect(
        "Coin",
        sorted(df["coin"].dropna().unique()),
        default=sorted(df["coin"].dropna().unique()),
    )
    account_options = sorted(df["account"].dropna().unique())
    accounts = st.multiselect("Account", account_options)
    min_trade_usd = st.slider(
        "Minimum trade size USD",
        min_value=0,
        max_value=int(df["size_usd"].quantile(0.99)),
        value=0,
        step=100,
    )

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = min_date
    end_date = max_date

filtered = df[
    (df["date"].dt.date >= start_date)
    & (df["date"].dt.date <= end_date)
    & (df["classification"].isin(sentiments))
    & (df["side_normalized"].isin(sides))
    & (df["coin"].isin(coins))
    & (df["size_usd"] >= min_trade_usd)
].copy()

if accounts:
    filtered = filtered[filtered["account"].isin(accounts)]

if filtered.empty:
    st.warning("No trades match the current filters.")
    st.stop()

total_trades = len(filtered)
total_volume = filtered["size_usd"].sum()
total_pnl = filtered["closed_pnl"].sum()
net_pnl = filtered["net_pnl"].sum()
win_rate = safe_rate(filtered["closed_pnl"])
avg_sentiment = filtered["sentiment_value"].mean()

kpi_cols = st.columns(6)
kpi_cols[0].metric("Trades", number(total_trades))
kpi_cols[1].metric("Volume", currency(total_volume))
kpi_cols[2].metric("Closed PnL", currency(total_pnl))
kpi_cols[3].metric("Net PnL", currency(net_pnl))
kpi_cols[4].metric("Win Rate", pct(win_rate))
kpi_cols[5].metric("Avg F/G", f"{avg_sentiment:.1f}")

tab_overview, tab_tracker, tab_segments, tab_accounts, tab_explorer = st.tabs(
    ["Overview", "Daily Tracker", "Segments", "Accounts", "Trade Explorer"]
)

with tab_overview:
    sentiment_summary = summarize(filtered, ["sentiment_group"])
    sentiment_summary["win_rate_pct"] = sentiment_summary["win_rate"] * 100

    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(
            bar_chart(
                sentiment_summary,
                "sentiment_group:N",
                "avg_pnl:Q",
                "sentiment_group:N",
                "Average PnL by Sentiment",
            ),
            use_container_width=True,
        )
    with col2:
        st.altair_chart(
            bar_chart(
                sentiment_summary,
                "sentiment_group:N",
                "win_rate_pct:Q",
                "sentiment_group:N",
                "Win Rate by Sentiment",
            ),
            use_container_width=True,
        )

    st.dataframe(
        sentiment_summary.sort_values("sentiment_group"),
        use_container_width=True,
        hide_index=True,
    )

with tab_tracker:
    daily = (
        filtered.groupby("date", as_index=False)
        .agg(
            trades=("trade_id", "count"),
            volume_usd=("size_usd", "sum"),
            closed_pnl=("closed_pnl", "sum"),
            net_pnl=("net_pnl", "sum"),
            sentiment_value=("sentiment_value", "mean"),
            win_rate=("closed_pnl", safe_rate),
        )
        .sort_values("date")
    )
    daily["cum_net_pnl"] = daily["net_pnl"].cumsum()
    daily["win_rate_pct"] = daily["win_rate"] * 100

    pnl_line = (
        alt.Chart(daily)
        .mark_line(point=False, color="#2F5597")
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("cum_net_pnl:Q", title="Cumulative net PnL"),
            tooltip=["date:T", "cum_net_pnl:Q", "net_pnl:Q", "sentiment_value:Q"],
        )
        .properties(title="Cumulative Net PnL Tracker", height=360)
    )
    sentiment_line = (
        alt.Chart(daily)
        .mark_line(point=False, color="#C55A11")
        .encode(
            x=alt.X("date:T"),
            y=alt.Y("sentiment_value:Q", title="Fear/Greed value"),
            tooltip=["date:T", "sentiment_value:Q"],
        )
    )
    st.altair_chart(
        alt.layer(pnl_line, sentiment_line).resolve_scale(y="independent"),
        use_container_width=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(
            alt.Chart(daily)
            .mark_bar(color="#5B8E7D")
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("net_pnl:Q", title="Daily net PnL"),
                tooltip=["date:T", "net_pnl:Q", "trades:Q", "win_rate_pct:Q"],
            )
            .properties(title="Daily Net PnL", height=320),
            use_container_width=True,
        )
    with col2:
        st.altair_chart(
            sentiment_line.properties(title="Fear/Greed Index", height=320),
            use_container_width=True,
        )

    st.dataframe(daily, use_container_width=True, hide_index=True)

with tab_segments:
    side_summary = summarize(filtered, ["sentiment_group", "side_normalized"])
    coin_summary = summarize(filtered, ["coin"]).sort_values("closed_pnl", ascending=False).head(25)
    hour_summary = summarize(filtered, ["hour"]).sort_values("hour")

    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(
            alt.Chart(side_summary)
            .mark_bar()
            .encode(
                x=alt.X("sentiment_group:N", sort=SENTIMENT_ORDER),
                y=alt.Y("closed_pnl:Q"),
                color="side_normalized:N",
                tooltip=list(side_summary.columns),
            )
            .properties(title="Closed PnL by Sentiment and Side", height=340),
            use_container_width=True,
        )
    with col2:
        st.altair_chart(
            alt.Chart(hour_summary)
            .mark_bar(color="#6C8EBF")
            .encode(
                x=alt.X("hour:O", title="Hour IST"),
                y=alt.Y("avg_pnl:Q", title="Average PnL"),
                tooltip=list(hour_summary.columns),
            )
            .properties(title="Average PnL by Hour", height=340),
            use_container_width=True,
        )

    st.subheader("Top Coins")
    st.altair_chart(
        alt.Chart(coin_summary)
        .mark_bar(color="#7A5195")
        .encode(
            x=alt.X("closed_pnl:Q", title="Closed PnL"),
            y=alt.Y("coin:N", sort="-x"),
            tooltip=list(coin_summary.columns),
        )
        .properties(height=520),
        use_container_width=True,
    )
    st.dataframe(side_summary, use_container_width=True, hide_index=True)

with tab_accounts:
    min_account_trades = st.slider("Minimum account trades", 1, 1000, 25, 5)
    account_summary = summarize(filtered, ["account"])
    account_summary = account_summary[account_summary["trades"] >= min_account_trades]
    account_summary = account_summary.sort_values("closed_pnl", ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Best Accounts")
        st.dataframe(account_summary.head(20), use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Worst Accounts")
        st.dataframe(
            account_summary.sort_values("closed_pnl").head(20),
            use_container_width=True,
            hide_index=True,
        )

    account_sentiment = summarize(filtered, ["account", "sentiment_group"])
    drilldown_options = account_summary["account"].head(100).tolist()
    selected_account = st.selectbox("Account drilldown", drilldown_options)
    if drilldown_options and selected_account:
        drilldown = account_sentiment[account_sentiment["account"] == selected_account]
        st.altair_chart(
            bar_chart(
                drilldown,
                "sentiment_group:N",
                "closed_pnl:Q",
                "sentiment_group:N",
                "Selected Account PnL by Sentiment",
            ),
            use_container_width=True,
        )

with tab_explorer:
    st.subheader("Filtered Trades")
    display_cols = [
        "trade_datetime_ist",
        "account",
        "coin",
        "side_normalized",
        "execution_price",
        "size_usd",
        "closed_pnl",
        "fee",
        "net_pnl",
        "classification",
        "sentiment_value",
        "transaction_hash",
    ]
    st.dataframe(
        filtered[display_cols].sort_values("trade_datetime_ist", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered trades",
        data=csv,
        file_name="filtered_trades.csv",
        mime="text/csv",
    )
