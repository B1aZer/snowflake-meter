## Experiment 1: the 60-second minimum

| pattern | queries | exec time (s) | wall span (min) | credits metered | $ | $ per query | vs batched |
|---|---|---|---|---|---|---|---|
| batched | 40 | 0.1 | 1.8 | 0.023 | 0.07 | 0.0017 | x1.0 |
| spread | 40 | 0.1 | 264.3 | 0.779 | 2.34 | 0.0584 | x33.6 |
| warm | 40 | 0.1 | 58.5 | 1.351 | 4.05 | 0.1013 | x58.2 |
| tight | 40 | 0.1 | 20.2 | 0.441 | 1.32 | 0.0330 | x19.0 |

rate-card reading: execution time x 1 credit/hour for X-Small. The 'credits metered' column is what the bill says.

## Experiment 2: TARGET_LAG = 1 minute, two hops

heartbeats sent 705 (one per 10 s); reader samples 1359 (one per 5 s)
age of the newest heartbeat visible at the far end: p50 32s, p90 52s, p99 59s, max 63s; share over the nominal 120 s (two hops x 1 min): 0.0%
Snowflake's own view of hb_far: target_lag_sec 60, mean_lag_sec None, maximum_lag_sec None, time_within_target_lag_ratio None (nulls = not reported while suspended)
hb_far refreshes on record: 100, of which NO_DATA (scheduled, nothing new): 26; window 2026-09-09 14:21:29.239000-07:00 -> 2026-09-09 15:40:40.503000-07:00

## Credits by warehouse (INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY, last 12 h)

  LEDGER_BATCHED: total 0.023 (compute 0.022, cloud services 0.001) = $0.07
  LEDGER_TIGHT: total 0.441 (compute 0.439, cloud services 0.001) = $1.32
  LEDGER_SPREAD: total 0.779 (compute 0.777, cloud services 0.002) = $2.34
  LEDGER_WARM: total 1.351 (compute 1.350, cloud services 0.001) = $4.05
  LEDGER_DT: total 2.859 (compute 2.713, cloud services 0.146) = $8.58
  COMPUTE_WH: total 0.434 (compute 0.432, cloud services 0.002) = $1.30
