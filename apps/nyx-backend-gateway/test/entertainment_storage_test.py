import tempfile
from pathlib import Path
import unittest

from nyx_backend_gateway.storage import (
    EntertainmentEvent,
    EntertainmentItem,
    create_connection,
    insert_entertainment_event,
    insert_entertainment_item,
    list_entertainment_events,
    list_entertainment_items,
)


class EntertainmentStorageTests(unittest.TestCase):
    def test_items_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            conn = create_connection(Path(tmp) / "gateway.db")
            insert_entertainment_item(
                conn,
                EntertainmentItem(
                    item_id="ent-001",
                    title="Signal Drift",
                    summary="Deterministic state steps for testnet alpha.",
                    category="pulse",
                ),
            )
            items = list_entertainment_items(conn)
            self.assertEqual(len(items), 1)
            insert_entertainment_event(
                conn,
                EntertainmentEvent(
                    event_id="event-1",
                    item_id="ent-001",
                    mode="pulse",
                    step=1,
                    run_id="run-1",
                ),
            )
            events = list_entertainment_events(conn, item_id="ent-001")
            self.assertEqual(len(events), 1)
            conn.close()


if __name__ == "__main__":
    unittest.main()
