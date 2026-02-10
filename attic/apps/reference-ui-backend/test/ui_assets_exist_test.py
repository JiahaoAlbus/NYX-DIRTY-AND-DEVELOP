from pathlib import Path
import unittest


class UIAssetsExistTests(unittest.TestCase):
    def test_ui_routes_exist(self):
        repo_root = Path(__file__).resolve().parents[3]
        static_dir = repo_root / "apps" / "reference-ui" / "static"
        routes = [
            "home.html",
            "ecosystem.html",
            "exchange.html",
            "chat.html",
            "protocol-library.html",
            "trust.html",
            "whitepaper.html",
            "status.html",
            "evidence.html",
        ]
        for name in routes:
            self.assertTrue((static_dir / name).exists())


if __name__ == "__main__":
    unittest.main()
