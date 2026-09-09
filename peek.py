from sf import connect, q
cx = connect(warehouse="COMPUTE_WH"); q(cx, "USE SCHEMA LEDGER.METER")
for wh in ["LEDGER_BATCHED", "LEDGER_TIGHT", "LEDGER_SPREAD", "LEDGER_DT"]:
    r = q(cx, "SELECT COUNT(*), COALESCE(SUM(credits_used),0), MIN(start_time), MAX(end_time) FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(DATEADD('hour', -6, CURRENT_TIMESTAMP()), CURRENT_TIMESTAMP(), %s))", (wh,))[0]
    print(wh, "hours-rows", r[0], "credits", float(r[1]), "window", r[2], "->", r[3])
