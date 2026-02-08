import os
import unittest

import _bootstrap  # noqa: F401
from nyx_backend_gateway.settings import SettingsError, get_settings

_KEYS = [
    "NYX_ENV",
    "NYX_PORTAL_SESSION_SECRET",
    "NYX_TESTNET_TREASURY_ADDRESS",
    "NYX_TESTNET_FEE_ADDRESS",
    "NYX_PLATFORM_FEE_BPS",
    "NYX_PROTOCOL_FEE_MIN",
    "NYX_FAUCET_COOLDOWN_SECONDS",
    "NYX_FAUCET_MAX_AMOUNT_PER_24H",
    "NYX_FAUCET_MAX_CLAIMS_PER_24H",
    "NYX_FAUCET_IP_MAX_CLAIMS_PER_24H",
    "NYX_0X_API_KEY",
    "NYX_JUPITER_API_KEY",
    "NYX_MAGIC_EDEN_API_KEY",
    "NYX_PAYEVM_API_KEY",
]


class SettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env = {key: os.environ.get(key) for key in _KEYS}

    def tearDown(self) -> None:
        for key, value in self._env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_dev_defaults_allow_missing_secret(self) -> None:
        os.environ["NYX_ENV"] = "dev"
        os.environ.pop("NYX_PORTAL_SESSION_SECRET", None)
        os.environ.pop("NYX_TESTNET_TREASURY_ADDRESS", None)
        os.environ.pop("NYX_TESTNET_FEE_ADDRESS", None)
        settings = get_settings()
        self.assertEqual(settings.env, "dev")
        self.assertTrue(settings.portal_session_secret)
        self.assertTrue(settings.treasury_address)

    def test_prod_requires_secret(self) -> None:
        os.environ["NYX_ENV"] = "prod"
        os.environ.pop("NYX_PORTAL_SESSION_SECRET", None)
        os.environ["NYX_TESTNET_TREASURY_ADDRESS"] = "0xdeadbeef"
        with self.assertRaises(SettingsError):
            get_settings()

    def test_prod_requires_treasury(self) -> None:
        os.environ["NYX_ENV"] = "prod"
        os.environ["NYX_PORTAL_SESSION_SECRET"] = "x" * 32
        os.environ.pop("NYX_TESTNET_TREASURY_ADDRESS", None)
        os.environ.pop("NYX_TESTNET_FEE_ADDRESS", None)
        with self.assertRaises(SettingsError):
            get_settings()

    def test_uuid_key_validation(self) -> None:
        os.environ["NYX_ENV"] = "dev"
        os.environ["NYX_0X_API_KEY"] = "not-a-uuid"
        with self.assertRaises(SettingsError):
            get_settings()


if __name__ == "__main__":
    unittest.main()
