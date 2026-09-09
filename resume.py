from sf import connect, q
cx = connect(warehouse="COMPUTE_WH"); q(cx, "USE SCHEMA LEDGER.METER")
for t in ["hb_near", "hb_far"]:
    q(cx, f"ALTER DYNAMIC TABLE {t} RESUME"); print("resumed", t)
