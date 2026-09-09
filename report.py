"""Read the meter. Credits per pattern from WAREHOUSE_METERING_HISTORY (the bill), execution
time per query from QUERY_HISTORY (what a rate card would suggest), and the lag tape.

ACCOUNT_USAGE lags by up to ~3 h, so run this a few hours after meter.py. The
INFORMATION_SCHEMA table function is fresher and is used as the primary source.

  python report.py
"""
import json
import os
import statistics as st

from sf import connect, q

CREDIT_USD = 3.0  # Enterprise list price per credit; change to your contract rate


def main():
    cx = connect(warehouse="COMPUTE_WH")
    q(cx, "USE SCHEMA LEDGER.METER")
    print("## Experiment 1: the 60-second minimum\n")
    print("| pattern | queries | exec time (s) | wall span (min) | credits metered | $ | $ per query | vs batched |")
    print("|---|---|---|---|---|---|---|---|")
    base = None
    for pat in ["batched", "spread", "warm", "tight"]:
        f = f"results/meter_{pat}.jsonl"
        if not os.path.exists(f):
            continue
        rows = [json.loads(l) for l in open(f)]
        wh = rows[0]["wh"]
        ids = [r["query_id"] for r in rows]
        exec_ms = q(cx, "SELECT COALESCE(SUM(execution_time),0) FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY_BY_WAREHOUSE(WAREHOUSE_NAME => %s, RESULT_LIMIT => 10000)) WHERE query_id IN (" + ",".join(["%s"] * len(ids)) + ")", [wh] + ids)[0][0]
        credits = q(cx, "SELECT COALESCE(SUM(credits_used),0) FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(DATEADD('day', -7, CURRENT_TIMESTAMP()), CURRENT_TIMESTAMP(), %s))", (wh,))[0][0]
        credits = float(credits)
        span = (rows[-1]["ts"] - rows[0]["ts"]) / 60
        usd = credits * CREDIT_USD
        per = usd / len(rows)
        if pat == "batched":
            base = per
        print(f"| {pat} | {len(rows)} | {float(exec_ms)/1000:.1f} | {span:.1f} | {credits:.3f} | {usd:.2f} | {per:.4f} | {('x%.1f' % (per/base)) if base else '-'} |")
    print("\nrate-card reading: execution time x 1 credit/hour for X-Small. The 'credits metered' column is what the bill says.")

    if os.path.exists("results/lag.jsonl"):
        seen = [json.loads(l) for l in open("results/lag.jsonl")]
        # 21:12-21:21 UTC on 2026-09-09: the dynamic tables were suspended by an early finisher run
        # and recreated on restart; those readings measure my mistake, not Snowflake. Excluded.
        bad = (1788988320, 1788988860)
        ages = [r["age_s"] for r in seen if r.get("kind") == "seen" and r.get("age_s") is not None and not (bad[0] <= r["ts"] <= bad[1])]
        sent = sum(1 for r in seen if r.get("kind") == "sent")
        if ages:
            ages.sort()
            p = lambda x: ages[min(len(ages) - 1, int(x * len(ages)))]
            print("\n## Experiment 2: TARGET_LAG = 1 minute, two hops\n")
            print(f"heartbeats sent {sent} (one per 10 s); reader samples {len(ages)} (one per 5 s)")
            print(f"age of the newest heartbeat visible at the far end: p50 {p(.5):.0f}s, p90 {p(.9):.0f}s, p99 {p(.99):.0f}s, max {ages[-1]:.0f}s; share over the nominal 120 s (two hops x 1 min): {100*sum(a>120 for a in ages)/len(ages):.1f}%")
            ref = q(cx, "SELECT target_lag_sec, mean_lag_sec, maximum_lag_sec, time_within_target_lag_ratio, scheduling_state FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLES(NAME => 'HB_FAR'))")[0]
            print(f"Snowflake's own view of hb_far: target_lag_sec {ref[0]}, mean_lag_sec {ref[1]}, maximum_lag_sec {ref[2]}, time_within_target_lag_ratio {ref[3]} (nulls = not reported while suspended)")
            hist = q(cx, "SELECT COUNT(*), SUM(IFF(refresh_action='NO_DATA',1,0)), MIN(refresh_start_time), MAX(refresh_start_time) FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(NAME => 'HB_FAR'))")[0]
            print(f"hb_far refreshes on record: {hist[0]}, of which NO_DATA (scheduled, nothing new): {hist[1]}; window {hist[2]} -> {hist[3]}")
    print("\n## Credits by warehouse (INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY, last 12 h)\n")
    for wh in ["LEDGER_BATCHED", "LEDGER_TIGHT", "LEDGER_SPREAD", "LEDGER_WARM", "LEDGER_DT", "COMPUTE_WH"]:
        r = q(cx, "SELECT COALESCE(SUM(credits_used),0), COALESCE(SUM(credits_used_compute),0), COALESCE(SUM(credits_used_cloud_services),0) FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(DATEADD('hour', -12, CURRENT_TIMESTAMP()), CURRENT_TIMESTAMP(), %s))", (wh,))[0]
        print(f"  {wh}: total {float(r[0]):.3f} (compute {float(r[1]):.3f}, cloud services {float(r[2]):.3f}) = ${float(r[0])*CREDIT_USD:.2f}")


if __name__ == "__main__":
    main()
