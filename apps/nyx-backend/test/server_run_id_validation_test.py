import json
import unittest
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC = BACKEND_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nyx_backend.server import GatewayHandler  # noqa: E402


class _FakeRequest(GatewayHandler):
    def __init__(self, body: bytes):
        self.rfile = BytesIO(body)
        self.wfile = BytesIO()
        self.headers = {"Content-Length": str(len(body))}
        self.responses = []

    def send_response(self, code, message=None):
        self.responses.append(code)

    def send_header(self, *_args, **_kwargs):
        pass

    def end_headers(self):
        pass


class ServerRunIdValidationTests(unittest.TestCase):
    def test_missing_run_id_returns_400(self) -> None:
        payload = json.dumps({"seed": 1, "module": "exchange", "action": "route_swap"}).encode("utf-8")
        handler = _FakeRequest(payload)
        handler.path = "/run"
        handler.do_POST()
        self.assertIn(HTTPStatus.BAD_REQUEST, handler.responses)


if __name__ == "__main__":
    unittest.main()
