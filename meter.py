"""Experiment 1: the 60-second minimum.

Same tiny query, same warehouse size, four traffic patterns. Each pattern gets its own
X-Small warehouse so the meter attributes credits cleanly:

  spread    : one query every 90 s, auto_suspend 60 s   -> a resume (and a 60 s bill) per query
  batched   : the same queries back to back              -> one resume
  warm      : one query every 90 s, auto_suspend 600 s   -> never suspends; pays for the gaps
  tight     : one query every 30 s, auto_suspend 60 s    -> never suspends either

Ground truth is read later by report.py from WAREHOUSE_METERING_HISTORY (credits) and
QUERY_HISTORY (execution time), so this script only produces the traffic and a local log.

  python meter.py --pattern spread --n 40
"""
import argparse
import json
import time

from sf import connect, ensure_db, q

PATTERNS = {
    "spread": {"gap_s": 90, "auto_suspend": 60},
    "batched": {"gap_s": 0, "auto_suspend": 60},
    "warm": {"gap_s": 90, "auto_suspend": 600},
    "tight": {"gap_s": 30, "auto_suspend": 60},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", required=True, choices=PATTERNS)
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    p = PATTERNS[a.pattern]
    wh = f"LEDGER_{a.pattern.upper()}"
    cx = connect(warehouse="COMPUTE_WH")  # the trial's default warehouse builds the probe table once
    ensure_db(cx)
    q(cx, "CREATE TABLE IF NOT EXISTS probe AS SELECT SEQ4() AS id, UNIFORM(1, 1000, RANDOM()) AS v FROM TABLE(GENERATOR(ROWCOUNT => 100000))")
    q(cx, f"CREATE WAREHOUSE IF NOT EXISTS {wh} WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = {p['auto_suspend']} AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE")
    q(cx, f"ALTER WAREHOUSE {wh} SET AUTO_SUSPEND = {p['auto_suspend']}")
    q(cx, f"USE WAREHOUSE {wh}")
    q(cx, "ALTER SESSION SET USE_CACHED_RESULT = FALSE")  # a cached result would not touch the warehouse
    log = open(f"results/meter_{a.pattern}.jsonl", "a")
    print(f"{a.pattern}: {a.n} queries, gap {p['gap_s']}s, auto_suspend {p['auto_suspend']}s, warehouse {wh}")
    for i in range(a.n):
        t0 = time.time()
        rows = q(cx, "SELECT SUM(v) FROM probe WHERE v > %s", (i % 900,))
        qid = q(cx, "SELECT LAST_QUERY_ID(-2)")[0][0]
        rec = {"pattern": a.pattern, "i": i, "ts": t0, "client_ms": round((time.time() - t0) * 1000), "query_id": qid, "wh": wh}
        log.write(json.dumps(rec) + "\n")
        log.flush()
        if i % 10 == 0:
            print(f"  {i}/{a.n} client {rec['client_ms']} ms")
        if p["gap_s"]:
            time.sleep(max(0, p["gap_s"] - (time.time() - t0)))
    q(cx, f"ALTER WAREHOUSE {wh} SUSPEND")
    print("done")


if __name__ == "__main__":
    main()
