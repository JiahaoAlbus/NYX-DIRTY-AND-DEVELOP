import _bootstrap
import base64
import tempfile
from pathlib import Path
import unittest

from nyx_backend_gateway import portal
from nyx_backend_gateway.storage import create_connection


class IdentityWalletInvariantTests(unittest.TestCase):
    def test_account_id_differs_from_handle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            conn = create_connection(db_path)
            try:
                key = b"invariant-key-0001"
                pubkey = base64.b64encode(key).decode("utf-8")
                account = portal.create_account(conn, handle="user_1", pubkey=pubkey)
                self.assertNotEqual(account.account_id, account.handle)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
