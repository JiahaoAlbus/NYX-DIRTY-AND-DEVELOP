import http.client
import json
import threading
import unittest

from nyx_reference_ui_backend.server import ReferenceUIHandler
from http.server import ThreadingHTTPServer


class ServerRunIdValidationTests(unittest.TestCase):
    def _start_server(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), ReferenceUIHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        return server, thread

    def _post_json(self, port, payload):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        body = json.dumps(payload).encode("utf-8")
        conn.request("POST", "/run", body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, data

    def test_missing_run_id_returns_400(self):
        server, thread = self._start_server()
        try:
            status, _ = self._post_json(server.server_port, {"seed": 123})
            self.assertEqual(status, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_invalid_run_id_returns_400(self):
        server, thread = self._start_server()
        try:
            status, _ = self._post_json(server.server_port, {"seed": 123, "run_id": "../"})
            self.assertEqual(status, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_long_run_id_returns_400(self):
        server, thread = self._start_server()
        try:
            long_id = "a" * 65
            status, _ = self._post_json(server.server_port, {"seed": 123, "run_id": long_id})
            self.assertEqual(status, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
