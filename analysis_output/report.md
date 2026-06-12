# Trader Performance vs Bitcoin Market Sentiment

## Executive Summary

This analysis merges Hyperliquid trade executions with the Bitcoin Fear/Greed Index by calendar date. It evaluates whether trader outcomes, volume, win rate, and side behavior change across sentiment regimes.

Key results:

- Trade rows analyzed: 211,224
- Rows matched to a sentiment day: 211,218 (100.0%)
- Trading date range: 2023-05-01 01:06 to 2025-05-01 12:13 IST
- Correlation between trade-level closed PnL and sentiment value: 0.0081
- Correlation between trade size USD and sentiment value: -0.0298
- Best average PnL sentiment regime: Extreme Greed (67.8929)
- Worst average PnL sentiment regime: Neutral (34.3077)
- Highest volume sentiment regime: Fear ($483,324,789.79)

## Method

1. Parsed trader timestamps from `Timestamp IST` and converted them to daily dates.
2. Parsed Fear/Greed dates from the sentiment dataset.
3. Left-joined trades to sentiment by date.
4. Calculated net PnL as `Closed PnL - Fee`, win rate as the share of trades with positive `Closed PnL`, and fee bps as `Fee / Size USD * 10000`.
5. Aggregated performance by sentiment classification, side, account, and day.

## Sentiment-Level Performance

| sentiment_group   |   trades |   accounts |   volume_usd |   avg_trade_usd |   total_closed_pnl |    total_net_pnl |   avg_closed_pnl |   median_closed_pnl |   win_rate |   avg_fee_bps |
|:------------------|---------:|-----------:|-------------:|----------------:|-------------------:|-----------------:|-----------------:|--------------------:|-----------:|--------------:|
| Extreme Fear      |    21400 |         32 |  1.14484e+08 |         5349.73 |   739110           | 715222           |          34.5379 |                   0 |   0.370607 |       2.13393 |
| Fear              |    61837 |         32 |  4.83325e+08 |         7816.11 |        3.35716e+06 |      3.2647e+06  |          54.2904 |                   0 |   0.420768 |       4.86945 |
| Neutral           |    37686 |         31 |  1.80242e+08 |         4782.73 |        1.29292e+06 |      1.25355e+06 |          34.3077 |                   0 |   0.396991 |       4.24652 |
| Greed             |    50303 |         31 |  2.88582e+08 |         5736.88 |        2.15013e+06 |      2.08703e+06 |          42.7436 |                   0 |   0.384828 |       2.55559 |
| Extreme Greed     |    39992 |         30 |  1.24465e+08 |         3112.25 |        2.71517e+06 |      2.68814e+06 |          67.8929 |                   0 |   0.464943 |       2.53776 |

## Side Behavior by Sentiment

| sentiment_group   | side_normalized   |   trades |   volume_usd |   total_closed_pnl |   avg_closed_pnl |   win_rate |
|:------------------|:------------------|---------:|-------------:|-------------------:|-----------------:|-----------:|
| Extreme Fear      | BUY               |    10935 |  5.6441e+07  |   373043           |          34.1146 |   0.201646 |
| Extreme Fear      | SELL              |    10465 |  5.80432e+07 |   366067           |          34.9801 |   0.547157 |
| Fear              | BUY               |    30270 |  2.46842e+08 |        1.93507e+06 |          63.9271 |   0.263    |
| Fear              | SELL              |    31567 |  2.36483e+08 |        1.42208e+06 |          45.0496 |   0.572053 |
| Neutral           | BUY               |    18969 |  7.36265e+07 |   554415           |          29.2274 |   0.240023 |
| Neutral           | SELL              |    18717 |  1.06616e+08 |   738506           |          39.4564 |   0.556072 |
| Greed             | BUY               |    24576 |  1.54988e+08 |   614457           |          25.0023 |   0.318075 |
| Greed             | SELL              |    25727 |  1.33594e+08 |        1.53567e+06 |          59.6911 |   0.448595 |
| Extreme Greed     | BUY               |    17940 |  6.03328e+07 |   188351           |          10.4989 |   0.311427 |
| Extreme Greed     | SELL              |    22052 |  6.41323e+07 |        2.52682e+06 |         114.585  |   0.589833 |

## Top Account/Sentiment Combinations

| account                                    | sentiment_group   |   trades |   volume_usd |   total_closed_pnl |    total_net_pnl |   win_rate |   avg_closed_pnl |
|:-------------------------------------------|:------------------|---------:|-------------:|-------------------:|-----------------:|-----------:|-----------------:|
| 0x083384f897ee0f19899168e3b1bec365f52a9012 | Fear              |     1778 |  3.02624e+07 |        1.11337e+06 |      1.11013e+06 |   0.526434 |         626.194  |
| 0xb1231a4a2dd02f2276fa3c5e2a2f3436e6bfed23 | Extreme Greed     |     1643 |  5.16153e+06 |        1.1053e+06  |      1.10378e+06 |   0.510043 |         672.736  |
| 0xbaaaf6571ab7d571043ff1e313a9609a10637864 | Fear              |    12437 |  4.0735e+07  |   620872           | 615230           |   0.498271 |          49.9214 |
| 0xb1231a4a2dd02f2276fa3c5e2a2f3436e6bfed23 | Greed             |     5889 |  3.6285e+07  |   534058           | 525962           |   0.273221 |          90.6874 |
| 0xbee1707d6b44d4d52bfe19e41f8a828645437aab | Extreme Greed     |     6723 |  1.65279e+07 |   478811           | 477137           |   0.596311 |          71.2199 |
| 0x72743ae2822edd658c0c50608fd7c5c501b2afbd | Greed             |      593 |  5.04964e+06 |   453595           | 453028           |   0.317032 |         764.916  |
| 0xb1231a4a2dd02f2276fa3c5e2a2f3436e6bfed23 | Neutral           |     3457 |  9.06415e+06 |   401309           | 398267           |   0.378073 |         116.086  |
| 0x513b8629fe877bb581bf244e326a047b249c4ff1 | Neutral           |     2517 |  6.97261e+07 |   381330           | 367920           |   0.554231 |         151.502  |
| 0x513b8629fe877bb581bf244e326a047b249c4ff1 | Fear              |     5981 |  2.25087e+08 |   367166           | 329571           |   0.370507 |          61.3888 |
| 0x4acb90e786d897ecffb614dc822eb231b4ffb9f4 | Fear              |     1396 |  1.82278e+07 |   296782           | 293175           |   0.409026 |         212.594  |

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
