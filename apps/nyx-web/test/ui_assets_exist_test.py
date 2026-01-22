import unittest
from pathlib import Path


class WebAssetsExistTests(unittest.TestCase):
    def test_required_routes_exist(self) -> None:
        root = Path(__file__).resolve().parents[1] / "static"
        routes = [
            "home",
            "world",
            "exchange",
            "chat",
            "marketplace",
            "entertainment",
            "trust",
            "protocol-library",
        ]
        for route in routes:
            page = root / route / "index.html"
            self.assertTrue(page.exists(), f"missing {route} page")

    def test_banner_present(self) -> None:
        root = Path(__file__).resolve().parents[1] / "static"
        page = (root / "home" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Week 2 Preview", page)
        self.assertIn("No live data", page)

    def test_exchange_script_exists(self) -> None:
        root = Path(__file__).resolve().parents[1] / "static"
        script = root / "js" / "exchange.js"
        self.assertTrue(script.exists(), "missing exchange.js")


if __name__ == "__main__":
    unittest.main()
