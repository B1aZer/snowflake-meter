# snowflake-meter

Two measured experiments on a Snowflake trial account, behind a Stays Up write-up.

1. `meter.py` — the 60-second minimum: the same 40 tiny queries under four traffic patterns, each on its own X-Small warehouse, credits read from `INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY`.
2. `lag.py` — TARGET_LAG measured against a heartbeat: a row every 10 s through two chained dynamic tables promising 1 minute each; a reader records the true age of the newest row at the far end every 5 s.

`report.py` prints both tables; `suspend.py` stops everything that bills. Auth is key-pair (`keys/`, gitignored) as a SERVICE user; the account identifier lives in `account.txt`.

Results from 2026-09-09 are in `results/REPORT.md` and the raw tapes in `results/*.jsonl`.
