"""Stop everything that could bill: suspend dynamic tables and every experiment warehouse."""
from sf import connect, q
cx = connect(warehouse="COMPUTE_WH"); q(cx, "USE SCHEMA LEDGER.METER")
for t in ["hb_far", "hb_near", "hb5_far", "hb5_near", "hb15_far", "hb15_near", "hbb_far", "hbb_near", "hb5b_far", "hb5b_near", "hb15b_far", "hb15b_near"]:
    try: q(cx, f"ALTER DYNAMIC TABLE {t} SUSPEND"); print("suspended", t)
    except Exception as e: print(t, e)
for wh in ["LEDGER_DT", "LEDGER_DT5", "LEDGER_DT15", "LEDGER_DTB", "LEDGER_DT5B", "LEDGER_DT15B", "LEDGER_IO", "LEDGER_BATCHED", "LEDGER_TIGHT", "LEDGER_SPREAD", "LEDGER_WARM", "COMPUTE_WH"]:
    try: q(cx, f"ALTER WAREHOUSE {wh} SUSPEND"); print("suspended", wh)
    except Exception as e: print(wh, str(e)[:80])
print(q(cx, "SHOW WAREHOUSES")[0][:3])
