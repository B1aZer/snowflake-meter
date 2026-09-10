"""The two questions to ask any Snowflake account before touching a warehouse:
  1. per warehouse: billed seconds vs seconds of actual query execution (last 7 days)
  2. per dynamic table: how many scheduled refreshes found nothing to do
Both read from INFORMATION_SCHEMA table functions, no extra tooling. Needs a role that can see
the warehouses; the trial's ACCOUNTADMIN can. Credits->seconds uses the X-Small rate (1 credit/h);
scale by warehouse size for larger ones."""
from sf import connect, q

cx = connect(warehouse="COMPUTE_WH")
q(cx, "USE SCHEMA LEDGER.METER")
print("| warehouse | credits 7d | billed seconds (XS rate) | executed seconds | billed / executed |")
print("|---|---|---|---|---|")
for (wh,) in q(cx, "SELECT DISTINCT warehouse_name FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(DATEADD('day',-6,CURRENT_TIMESTAMP()))) ORDER BY 1"):
    cr = float(q(cx, "SELECT COALESCE(SUM(credits_used_compute),0) FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(DATEADD('day',-6,CURRENT_TIMESTAMP()), CURRENT_TIMESTAMP(), %s))", (wh,))[0][0])
    ex = float(q(cx, "SELECT COALESCE(SUM(execution_time),0)/1000 FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY_BY_WAREHOUSE(WAREHOUSE_NAME => %s, END_TIME_RANGE_START => DATEADD('day',-6,CURRENT_TIMESTAMP()), RESULT_LIMIT => 10000))", (wh,))[0][0])
    billed = cr * 3600
    print(f"| {wh} | {cr:.3f} | {billed:,.0f} | {ex:,.1f} | {'x%.0f' % (billed/ex) if ex else 'n/a'} |")
print()
print("| dynamic table | refreshes | NO_DATA | share |")
print("|---|---|---|---|")
for (name,) in q(cx, "SELECT name FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLES()) ORDER BY 1"):
    r = q(cx, "SELECT COUNT(*), SUM(IFF(refresh_action='NO_DATA',1,0)) FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(NAME => %s))", (name,))[0]
    n, nd = int(r[0] or 0), int(r[1] or 0)
    print(f"| {name} | {n} | {nd} | {('%.0f%%' % (100*nd/n)) if n else 'n/a'} |")
