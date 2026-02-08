import _bootstrap
import unittest

from nyx_backend_gateway.errors import GatewayApiError
from nyx_backend_gateway import web2_guard


class Web2GuardUnitTests(unittest.TestCase):
    def test_ip_literal_denied(self) -> None:
        with self.assertRaises(GatewayApiError) as ctx:
            web2_guard._web2_match_allowlist("https://127.0.0.1/", "GET")
        self.assertEqual(ctx.exception.code, "ALLOWLIST_DENY")

    def test_http_scheme_denied(self) -> None:
        with self.assertRaises(GatewayApiError) as ctx:
            web2_guard._web2_match_allowlist("http://api.github.com/zen", "GET")
        self.assertEqual(ctx.exception.code, "ALLOWLIST_DENY")

    def test_method_not_allowlisted_denied(self) -> None:
        with self.assertRaises(GatewayApiError) as ctx:
            web2_guard._web2_match_allowlist("https://api.github.com/zen", "POST")
        self.assertEqual(ctx.exception.code, "ALLOWLIST_DENY")

    def test_path_traversal_denied(self) -> None:
        with self.assertRaises(GatewayApiError) as ctx:
            web2_guard._web2_match_allowlist("https://api.github.com/../secret", "GET")
        self.assertEqual(ctx.exception.code, "ALLOWLIST_DENY")

    def test_private_host_resolution_denied(self) -> None:
        with self.assertRaises(GatewayApiError):
            web2_guard._web2_resolve_public_host("localhost")

    def test_body_size_limit_enforced(self) -> None:
        oversized = "x" * (web2_guard._WEB2_MAX_BODY_BYTES + 1)
        with self.assertRaises(GatewayApiError):
            web2_guard._coerce_web2_body(oversized)


if __name__ == "__main__":
    unittest.main()
