"""Stop everything that could bill: suspend dynamic tables and every experiment warehouse."""
from sf import connect, q
cx = connect(warehouse="COMPUTE_WH"); q(cx, "USE SCHEMA LEDGER.METER")
for t in ["hb_far", "hb_near"]:
    try: q(cx, f"ALTER DYNAMIC TABLE {t} SUSPEND"); print("suspended", t)
    except Exception as e: print(t, e)
for wh in ["LEDGER_DT", "LEDGER_BATCHED", "LEDGER_TIGHT", "LEDGER_SPREAD", "LEDGER_WARM", "COMPUTE_WH"]:
    try: q(cx, f"ALTER WAREHOUSE {wh} SUSPEND"); print("suspended", wh)
    except Exception as e: print(wh, str(e)[:80])
print(q(cx, "SHOW WAREHOUSES")[0][:3])
