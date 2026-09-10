import sys
from sf import connect, q
cx = connect(warehouse="COMPUTE_WH"); q(cx, "USE SCHEMA LEDGER.METER")
sql = open(sys.argv[1]).read()
try:
    for r in q(cx, sql): print(r)
except Exception as e:
    print("ERROR:", str(e)[:300])
