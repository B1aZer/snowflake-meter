"""Connection + tiny helpers. Key-pair auth: the private key stays in keys/ (gitignored),
the account identifier comes from $SNOWFLAKE_ACCOUNT or account.txt (gitignored)."""
import os
import snowflake.connector
from cryptography.hazmat.primitives import serialization

HERE = os.path.dirname(os.path.abspath(__file__))


def _pkey():
    with open(os.path.join(HERE, "keys", "ledger_bot.p8"), "rb") as f:
        k = serialization.load_pem_private_key(f.read(), password=None)
    return k.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())


class Conn:
    """Thin wrapper: key-pair sessions expire after ~1 h and the connector does not renew them,
    so q() reconnects and replays the session context on error 390114."""

    def __init__(self, warehouse, role):
        self.warehouse, self.role, self.schema = warehouse, role, None
        self._open()

    def _open(self):
        account = os.environ.get("SNOWFLAKE_ACCOUNT") or open(os.path.join(HERE, "account.txt")).read().strip()
        self.raw = snowflake.connector.connect(
            account=account, user=os.environ.get("SNOWFLAKE_USER", "LEDGER_BOT"),
            private_key=_pkey(), role=self.role, warehouse=self.warehouse, client_session_keep_alive=True,
        )
        if self.schema:
            self.raw.cursor().execute(f"USE SCHEMA {self.schema}")

    def cursor(self):
        return self.raw.cursor()


def connect(warehouse=None, role="ACCOUNTADMIN"):
    return Conn(warehouse, role)


def q(cx, sql, params=None):
    for attempt in (1, 2):
        cur = cx.cursor()
        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
            u = sql.strip().upper()
            if u.startswith("USE SCHEMA"):
                cx.schema = sql.split()[-1]
            if u.startswith("USE WAREHOUSE"):
                cx.warehouse = sql.split()[-1]
            return rows
        except snowflake.connector.errors.ProgrammingError as e:
            if attempt == 1 and e.errno in (390114, 390111, 390112):
                cx._open()
                continue
            raise
        finally:
            cur.close()


def ensure_db(cx):
    q(cx, "CREATE DATABASE IF NOT EXISTS LEDGER")
    q(cx, "CREATE SCHEMA IF NOT EXISTS LEDGER.METER")
    q(cx, "USE SCHEMA LEDGER.METER")
