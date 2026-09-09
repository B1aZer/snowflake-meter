from sf import connect, q, ensure_db
cx = connect(warehouse="COMPUTE_WH")
ensure_db(cx)
print(q(cx, "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME(), CURRENT_REGION()"))
print("credits used so far:", q(cx, "SELECT COALESCE(SUM(credits_used),0) FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(DATEADD('day',-30,CURRENT_TIMESTAMP())))"))
