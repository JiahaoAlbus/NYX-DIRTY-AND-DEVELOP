import _bootstrap
import sqlite3
import tempfile
from pathlib import Path
import unittest

from nyx_backend_gateway.migrations import apply_migrations


class StorageMigrationTests(unittest.TestCase):
    def test_tables_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            conn = sqlite3.connect(str(db_path))
            apply_migrations(conn)
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            expected = {
                "meta",
                "evidence_runs",
                "orders",
                "trades",
                "messages",
                "listings",
                "purchases",
                "receipts",
            }
            self.assertTrue(expected.issubset(tables))
            conn.close()


if __name__ == "__main__":
    unittest.main()
