import json
import os
import socket
import subprocess
import sys
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def _healthz_ok(port: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            conn = HTTPConnection("127.0.0.1", port, timeout=2)
            conn.request("GET", "/healthz")
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            conn.close()
            if resp.status == 200 and "\"ok\":true" in body.replace(" ", ""):
                return True
        except Exception:
            time.sleep(0.2)
    return False


class DevLauncherSmokeTests(unittest.TestCase):
    def test_dev_launcher_imports_backend(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        env = os.environ.copy()
        env["PYTHONPATH"] = (
            f"{repo_root / 'apps' / 'nyx-backend-gateway' / 'src'}:{repo_root / 'apps' / 'nyx-backend' / 'src'}"
        )
        result = subprocess.run(
            [sys.executable, "-c", "import nyx_backend"],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_dev_launcher_wallet_faucet(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        script = repo_root / "scripts" / "nyx_backend_dev.sh"
        env = os.environ.copy()
        env.setdefault("NYX_TESTNET_TREASURY_ADDRESS", "testnet-treasury-addr")
        env.setdefault("NYX_PROTOCOL_FEE_MIN", "1")
        env["NYX_DEV_NO_VENV"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env["NYX_DEV_PORT"] = str(port)
        run_id = f"dev-launcher-faucet-{port}"
        proc = subprocess.Popen(
            ["bash", str(script)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            if not _wait_for_port("127.0.0.1", port, timeout=10.0):
                proc.terminate()
                out, err = proc.communicate(timeout=2)
                self.fail(f"backend dev launcher did not bind 127.0.0.1:{port}\n{out}\n{err}")
            if not _healthz_ok(port, timeout=5.0):
                proc.terminate()
                out, err = proc.communicate(timeout=2)
                self.fail(f"backend did not become healthy\n{out}\n{err}")
            conn = HTTPConnection("127.0.0.1", port, timeout=10)
            payload = {
                "seed": 123,
                "run_id": run_id,
                "payload": {"address": "wallet-dev", "amount": 10},
            }
            conn.request("POST", "/wallet/faucet", body=json.dumps(payload), headers={"Content-Type": "application/json"})
            try:
                resp = conn.getresponse()
                body = resp.read()
                self.assertEqual(resp.status, 200, body.decode("utf-8"))
                parsed = json.loads(body.decode("utf-8"))
                self.assertEqual(parsed.get("status"), "complete")
                conn.close()
            except Exception as exc:
                proc.terminate()
                try:
                    out, err = proc.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    out, err = proc.communicate()
                self.fail(f"faucet request failed: {exc}\n{out}\n{err}")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    unittest.main()
