# snowflake-meter

Two measured experiments on a Snowflake trial account. They back the write-up at
[staysup.io/snowflake-meter](https://staysup.io/snowflake-meter).

1. `meter.py`, the 60-second minimum: the same 40 tiny queries under four traffic patterns, each on its own X-Small warehouse. Credits are read from `INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY`.
2. `lag.py`, TARGET_LAG against a heartbeat: a row every 10 s goes through two chained dynamic tables, and a reader records the true age of the newest row at the far end every 5 s.

## Results

Full tables are in [`results/REPORT.md`](results/REPORT.md); the raw tapes are `results/*.jsonl`.

**The 60-second minimum.** 40 queries, 0.1 s of total execution each run:

| pattern | how | credits | vs batched |
|---|---|---|---|
| batched | back to back | 0.023 | x1 |
| tight | one every 30 s, auto_suspend 60 s | 0.441 | x19 |
| spread | one every 90 s, auto_suspend 60 s | 0.779 | x34 |
| warm | one every 90 s, auto_suspend 600 s | 1.351 | x58 |

**TARGET_LAG.** Two hops, 45 minutes per setting, dynamic tables on their own warehouse:

| TARGET_LAG per hop | p50 age | p90 age | DT credits per hour |
|---|---|---|---|
| 1 min | 35 s | 52 s | 1.35 |
| 5 min | 106 s | 184 s | 0.50 |
| 15 min | 379 s | 700 s | 0.16 |

The first design put the heartbeat writer and reader on the same warehouse as the dynamic tables.
That kept the warehouse awake and made refresh cost look flat at about 1.4 credits/hour whatever the lag.
The curve above is the rerun with the probe on its own warehouse (`--io-warehouse`). Snowflake bills per
warehouse, so a probe that shares one becomes part of what it measures.

## Checking your own account

`ratio_query.sql` compares billed seconds with executed seconds per warehouse over the last 6 days.
`empty_refresh_query.sql` counts dynamic-table refreshes that found nothing new. `diagnose.py` asks the same two questions from Python, one warehouse and one dynamic table at a time.
Both queries use only `INFORMATION_SCHEMA` table functions.

## Reproducing

Python 3.12. Auth is key-pair as a SERVICE user; new accounts require MFA for password logins, so this is the scriptable path.

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
mkdir -p keys
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out keys/ledger_bot.p8 -nocrypt
openssl rsa -in keys/ledger_bot.p8 -pubout -out keys/ledger_bot.pub
```

In a Snowflake worksheet, paste the body of `keys/ledger_bot.pub` without the header lines:

```sql
CREATE USER LEDGER_BOT TYPE = SERVICE RSA_PUBLIC_KEY = '<public key body>' DEFAULT_ROLE = ACCOUNTADMIN;
GRANT ROLE ACCOUNTADMIN TO USER LEDGER_BOT;
```

Then:

```bash
export SNOWFLAKE_ACCOUNT=<orgname-accountname>   # or put it in account.txt (gitignored)
./run.sh meter.py --pattern spread --n 40         # one pattern
./run_all.sh                                      # all four patterns + a 2 h heartbeat
./run_lagcurve.sh                                 # TARGET_LAG 1/5/15 min, 45 min each
./run.sh report.py                                # prints the tables
./run.sh suspend.py                               # stops everything that bills
```

The scripts create the `LEDGER` database, the warehouses and the dynamic tables themselves. The runs in `results/REPORT.md`
add up to about 11.7 credits of a trial's allowance. Run `suspend.py` when you're done: dynamic tables keep refreshing,
and billing, until they are suspended.

## License

MIT. See [LICENSE](LICENSE).
