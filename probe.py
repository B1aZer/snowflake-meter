from sf import connect, q
cx = connect(warehouse="COMPUTE_WH"); q(cx, "USE SCHEMA LEDGER.METER")
cur = cx.cursor(); cur.execute("SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLES(NAME => 'HB_FAR'))")
cols=[d[0] for d in cur.description]; row=cur.fetchone(); print(dict(zip(cols,row)))
print("--- credits by warehouse (12h)")
for wh in ["LEDGER_BATCHED","LEDGER_TIGHT","LEDGER_SPREAD","LEDGER_WARM","LEDGER_DT","COMPUTE_WH"]:
    r=q(cx,"SELECT COALESCE(SUM(credits_used),0), COALESCE(SUM(credits_used_compute),0), COALESCE(SUM(credits_used_cloud_services),0) FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(DATEADD('hour',-12,CURRENT_TIMESTAMP()),CURRENT_TIMESTAMP(),%s))",(wh,))[0]
    print(f"  {wh}: total {float(r[0]):.3f} compute {float(r[1]):.3f} cloud {float(r[2]):.3f}")
print("--- DT refresh history (hb_far, last 20)")
for r in q(cx,"SELECT refresh_start_time, refresh_end_time, state, refresh_action, refresh_trigger FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(NAME => 'HB_FAR')) ORDER BY refresh_start_time DESC LIMIT 12"): print("  ", r)
