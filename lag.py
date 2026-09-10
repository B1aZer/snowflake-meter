"""Experiment 2: TARGET_LAG, measured against what.

A heartbeat row lands in a source table every 10 s with the client's clock. Two chained
dynamic tables promise TARGET_LAG = 1 minute each. A reader polls the far end every 5 s and
records the true age of the newest heartbeat it can see: that is the freshness a consumer
actually gets, versus the two minutes the settings imply.

  python lag.py --minutes 120
"""
import argparse
import json
import threading
import time

from sf import connect, ensure_db, q



def writer(stop, log, WH, tag):
    cx = connect(warehouse=WH)  # WH here is the probe's own warehouse, never the dynamic tables' one
    q(cx, "USE SCHEMA LEDGER.METER")
    while not stop.is_set():
        t = time.time()
        q(cx, f"INSERT INTO heartbeat{tag}(sent_epoch) VALUES (%s)", (t,))
        log.write(json.dumps({"kind": "sent", "ts": t}) + "\n")
        time.sleep(max(0, 10 - (time.time() - t)))


def reader(stop, log, WH, tag):
    cx = connect(warehouse=WH)
    q(cx, "USE SCHEMA LEDGER.METER")
    q(cx, "ALTER SESSION SET USE_CACHED_RESULT = FALSE")
    while not stop.is_set():
        t = time.time()
        rows = q(cx, f"SELECT MAX(sent_epoch) FROM hb{tag}_far")
        newest = rows[0][0]
        age = (t - float(newest)) if newest is not None else None
        log.write(json.dumps({"kind": "seen", "ts": t, "newest": newest, "age_s": age}) + "\n")
        log.flush()
        time.sleep(max(0, 5 - (time.time() - t)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=120)
    ap.add_argument("--lag-minutes", type=int, default=1, help="TARGET_LAG per hop")
    ap.add_argument("--suffix", default="", help="object-name suffix for a fresh run (e.g. b)")
    ap.add_argument("--io-warehouse", default="LEDGER_IO", help="warehouse for the heartbeat writer and reader; the dynamic tables get their own so refresh cost is attributable")
    a = ap.parse_args()
    tag = ("" if a.lag_minutes == 1 else f"{a.lag_minutes}") + a.suffix
    WH = "LEDGER_DT" + tag          # dynamic tables only
    IO = a.io_warehouse             # probe traffic only
    cx = connect()
    ensure_db(cx)
    q(cx, f"CREATE WAREHOUSE IF NOT EXISTS {WH} WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE")
    q(cx, f"CREATE WAREHOUSE IF NOT EXISTS {IO} WAREHOUSE_SIZE = XSMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE")
    q(cx, f"CREATE TABLE IF NOT EXISTS heartbeat{tag} (sent_epoch DOUBLE, inserted_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())")
    q(cx, f"CREATE OR REPLACE DYNAMIC TABLE hb{tag}_near TARGET_LAG = '{a.lag_minutes} minute' WAREHOUSE = {WH} AS SELECT sent_epoch, inserted_at FROM heartbeat{tag}")
    q(cx, f"CREATE OR REPLACE DYNAMIC TABLE hb{tag}_far TARGET_LAG = '{a.lag_minutes} minute' WAREHOUSE = {WH} AS SELECT sent_epoch, inserted_at FROM hb{tag}_near")
    print(f"dynamic tables ready (TARGET_LAG {a.lag_minutes} min, DT warehouse {WH}, probe warehouse {IO}); running {a.minutes} min")
    log = open(f"results/lag{tag}.jsonl", "a")
    stop = threading.Event()
    ts = [threading.Thread(target=writer, args=(stop, log, IO, tag), daemon=True), threading.Thread(target=reader, args=(stop, log, IO, tag), daemon=True)]
    for t in ts:
        t.start()
    try:
        time.sleep(a.minutes * 60)
    finally:
        stop.set()
        for t in ts:
            t.join(timeout=30)
    print("done")


if __name__ == "__main__":
    main()
