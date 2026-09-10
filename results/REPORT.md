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

## Experiment 3: the TARGET_LAG curve (two chained hops, 45 min each, dynamic tables on their own warehouse; probe writer/reader on LEDGER_IO)

| TARGET_LAG per hop | nominal worst case | heartbeats | p50 age | p90 age | max age | refreshes (far) | NO_DATA | DT warehouse compute credits | per hour |
|---|---|---|---|---|---|---|---|---|---|
| 1 min | 2 min | 256 | 35 s | 52 s | 179 s | 61 | 5 | 1.005 | 1.35 |
| 5 min | 10 min | 256 | 106 s | 184 s | 205 s | 16 | 0 | 0.373 | 0.50 |
| 15 min | 30 min | 256 | 379 s | 700 s | 777 s | 5 | 0 | 0.117 | 0.16 |

probe traffic (one INSERT per 10 s + one SELECT per 5 s, three runs in parallel) on LEDGER_IO: 1.004 compute credits over the window 2026-09-10T20:52:24Z -> 2026-09-10T21:37:37Z; this is the cost the first design wrongly attributed to the dynamic tables.

First-design run for reference (probe on the same warehouse as the DTs, TARGET_LAG 1 min, ~2 h): LEDGER_DT 2.713 compute credits; 5 and 15 min one-hour runs: 1.390 and 1.374. Flat because the probe kept the warehouse awake regardless of lag.

## Credits by warehouse (INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY, last 12 h)

  LEDGER_BATCHED: total 0.023 (compute 0.022, cloud services 0.001) = $0.07
  LEDGER_TIGHT: total 0.441 (compute 0.439, cloud services 0.001) = $1.32
  LEDGER_SPREAD: total 0.779 (compute 0.777, cloud services 0.002) = $2.34
  LEDGER_WARM: total 1.351 (compute 1.350, cloud services 0.001) = $4.05
  LEDGER_DT: total 2.860 (compute 2.713, cloud services 0.147) = $8.58
  LEDGER_DT5: total 1.425 (compute 1.390, cloud services 0.035) = $4.27
  LEDGER_DT15: total 1.402 (compute 1.374, cloud services 0.028) = $4.20
  LEDGER_DTB: total 1.020 (compute 1.005, cloud services 0.015) = $3.06
  LEDGER_DT5B: total 0.377 (compute 0.373, cloud services 0.004) = $1.13
  LEDGER_DT15B: total 0.118 (compute 0.117, cloud services 0.001) = $0.36
  LEDGER_IO: total 1.060 (compute 1.004, cloud services 0.056) = $3.18
  COMPUTE_WH: total 0.847 (compute 0.840, cloud services 0.007) = $2.54
