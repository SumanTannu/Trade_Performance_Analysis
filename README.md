# Bitcoin Sentiment vs Hyperliquid Trader Performance

This workspace contains a reproducible first-step analysis for the hiring assignment.

## Files

- `historical_data.csv`: Hyperliquid trader execution data.
- `fear_greed_index.csv`: Bitcoin Fear/Greed Index history.
- `analyze_sentiment_trader.py`: Reproducible analysis script.
- `streamlit_app.py`: Interactive dashboard for filtering and visual exploration.
- `analysis_output/report.md`: Main written report with methodology, findings, and strategy ideas.
- `analysis_output/*.csv`: Merged dataset and summary tables.
- `analysis_output/*.png`: Visual summaries.
- `requirements.txt`: Python dependencies for the analysis and dashboard.

## How to Run

```powershell
python analyze_sentiment_trader.py
```

The script writes all generated files to `analysis_output/`.

## How to Run the Dashboard

Install dependencies if needed:

```powershell
pip install -r requirements.txt
```

Launch Streamlit:

```powershell
streamlit run streamlit_app.py
```

The dashboard includes:

- Portfolio KPIs for trades, volume, closed PnL, net PnL, win rate, and average Fear/Greed value.
- Interactive filters for date range, sentiment, side, coin, account, and minimum trade size.
- Sentiment-level performance charts.
- Daily cumulative net PnL tracker with Fear/Greed overlay.
- Side, coin, and hour-of-day segment analysis.
- Best/worst account tables and account-level sentiment drilldown.
- Filtered trade explorer with CSV download.

## Notes

- Trades are joined to sentiment by the calendar date parsed from `Timestamp IST`.
- Net PnL is calculated as `Closed PnL - Fee`.
- Win rate is the share of trade rows where `Closed PnL > 0`.
- Median closed PnL is zero across sentiment buckets, which indicates a skewed distribution with many zero-PnL rows. Average PnL and win rate should therefore be interpreted together rather than in isolation.
