import base64
import hmac
import json
import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

import _bootstrap  # noqa: F401
import nyx_backend_gateway.gateway as gateway
import nyx_backend_gateway.server as server
from nyx_backend_gateway.identifiers import order_id


class ServerConcurrencyTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["NYX_TESTNET_FEE_ADDRESS"] = "testnet-fee-address"
        os.environ.pop("NYX_TESTNET_TREASURY_ADDRESS", None)
        os.environ["NYX_FAUCET_COOLDOWN_SECONDS"] = "0"
        os.environ["NYX_FAUCET_MAX_AMOUNT_PER_24H"] = "0"
        os.environ["NYX_FAUCET_MAX_CLAIMS_PER_24H"] = "0"
        os.environ["NYX_FAUCET_IP_MAX_CLAIMS_PER_24H"] = "0"
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "gateway.db"
        self.run_root = Path(self.tmp.name) / "runs"
        gateway._db_path = lambda: self.db_path
        gateway._run_root = lambda: self.run_root
        server._db_path = lambda: self.db_path
        server._run_root = lambda: self.run_root
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.GatewayHandler)
        self.httpd.rate_limiter = server.RequestLimiter(200, 60)
        self.httpd.account_limiter = server.RequestLimiter(200, 60)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_address[1]

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.thread.join(timeout=2)
        self.httpd.server_close()
        self.tmp.cleanup()

    def _post(self, path: str, payload: dict, token: str | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        body = json.dumps(payload, separators=(",", ":"))
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, json.loads(data.decode("utf-8"))

    def _get(self, path: str, token: str | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, json.loads(data.decode("utf-8"))

    def _auth_token(self, handle: str) -> tuple[str, str, str]:
        key = f"portal-key-{handle}-0001".encode("utf-8")
        pubkey = base64.b64encode(key).decode("utf-8")
        status, created = self._post("/portal/v1/accounts", {"handle": handle, "pubkey": pubkey})
        self.assertEqual(status, 200)
        account_id = created.get("account_id")
        wallet_address = created.get("wallet_address")
        status, challenge = self._post("/portal/v1/auth/challenge", {"account_id": account_id})
        self.assertEqual(status, 200)
        nonce = challenge.get("nonce")
        signature = base64.b64encode(hmac.new(key, nonce.encode("utf-8"), "sha256").digest()).decode("utf-8")
        status, verified = self._post(
            "/portal/v1/auth/verify",
            {"account_id": account_id, "nonce": nonce, "signature": signature},
        )
        self.assertEqual(status, 200)
        return account_id, wallet_address, verified.get("access_token")

    def test_concurrent_wallet_transfers_enforce_fees(self) -> None:
        _, wallet_a, token_a = self._auth_token("conc_a")
        _, wallet_b, token_b = self._auth_token("conc_b")

        status, _ = self._post(
            "/wallet/v1/faucet",
            {"seed": 123, "run_id": "conc-faucet-a", "payload": {"address": wallet_a, "amount": 5000}},
            token=token_a,
        )
        self.assertEqual(status, 200)

        results: list[tuple[int, dict]] = []
        lock = threading.Lock()

        def run_transfer(idx: int) -> None:
            st, res = self._post(
                "/wallet/v1/transfer",
                {
                    "seed": 123,
                    "run_id": f"conc-transfer-{idx}",
                    "payload": {"from_address": wallet_a, "to_address": wallet_b, "amount": 10, "asset_id": "NYXT"},
                },
                token=token_a,
            )
            with lock:
                results.append((st, res))

        threads = [threading.Thread(target=run_transfer, args=(i,)) for i in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        self.assertEqual(len(results), 6)
        for status, payload in results:
            self.assertEqual(status, 200)
            self.assertGreater(payload.get("fee_total", 0), 0)

        status, a_bal = self._get(f"/wallet/v1/balances?address={wallet_a}", token=token_a)
        self.assertEqual(status, 200)
        status, b_bal = self._get(f"/wallet/v1/balances?address={wallet_b}", token=token_b)
        self.assertEqual(status, 200)

        a_nyxt = next((row["balance"] for row in a_bal.get("balances", []) if row.get("asset_id") == "NYXT"), 0)
        b_nyxt = next((row["balance"] for row in b_bal.get("balances", []) if row.get("asset_id") == "NYXT"), 0)

        transferred = 6 * 10
        self.assertEqual(b_nyxt, transferred)
        self.assertLess(a_nyxt, 5000 - transferred)

    def test_concurrent_order_cancellations(self) -> None:
        _, wallet_address, token = self._auth_token("order_a")

        status, _ = self._post(
            "/wallet/v1/faucet",
            {"seed": 321, "run_id": "conc-order-faucet", "payload": {"address": wallet_address, "amount": 8000}},
            token=token,
        )
        self.assertEqual(status, 200)

        order_ids: list[str] = []
        for idx in range(4):
            run_id = f"conc-order-{idx}"
            status, placed = self._post(
                "/exchange/place_order",
                {
                    "seed": 321,
                    "run_id": run_id,
                    "payload": {
                        "side": "SELL",
                        "amount": 10,
                        "price": 2,
                        "asset_in": "NYXT",
                        "asset_out": "ECHO",
                        "owner_address": wallet_address,
                    },
                },
                token=token,
            )
            self.assertEqual(status, 200)
            order_ids.append(order_id(run_id))

        results: list[tuple[int, dict]] = []
        lock = threading.Lock()

        def cancel_order(idx: int, order_id: str) -> None:
            st, res = self._post(
                "/exchange/cancel_order",
                {"seed": 321, "run_id": f"conc-cancel-{idx}", "payload": {"order_id": order_id}},
                token=token,
            )
            with lock:
                results.append((st, res))

        threads = [threading.Thread(target=cancel_order, args=(i, oid)) for i, oid in enumerate(order_ids)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        self.assertEqual(len(results), len(order_ids))
        for status, payload in results:
            self.assertEqual(status, 200)
            self.assertGreater(payload.get("fee_total", 0), 0)

        status, my_orders = self._get("/exchange/v1/my_orders?status=cancelled&limit=10", token=token)
        self.assertEqual(status, 200)
        cancelled = {row.get("order_id") for row in my_orders.get("orders", [])}
        self.assertTrue(set(order_ids).issubset(cancelled))


if __name__ == "__main__":
    unittest.main()
