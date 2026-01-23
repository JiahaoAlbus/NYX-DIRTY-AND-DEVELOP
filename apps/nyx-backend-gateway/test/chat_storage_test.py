import _bootstrap
import tempfile
from pathlib import Path
import unittest

from nyx_backend_gateway.storage import MessageEvent, create_connection, insert_message_event, list_messages


class ChatStorageTests(unittest.TestCase):
    def test_list_messages_by_channel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            conn = create_connection(Path(tmp) / "gateway.db")
            insert_message_event(
                conn,
                MessageEvent(message_id="m1", channel="general", body="hello", run_id="run-1"),
            )
            insert_message_event(
                conn,
                MessageEvent(message_id="m2", channel="alpha", body="ping", run_id="run-2"),
            )
            messages = list_messages(conn, channel="general")
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0]["channel"], "general")
            conn.close()


if __name__ == "__main__":
    unittest.main()
