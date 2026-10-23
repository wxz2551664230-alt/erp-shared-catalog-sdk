import json
from pathlib import Path
import unittest

from client import CatalogClient, from_ozon_submission


class Response:
    status_code = 200
    def __init__(self, value): self.value = value
    def json(self): return self.value


class Session:
    def __init__(self): self.calls = []; self.closed = False
    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return Response({"version": 1} if url.endswith("/capabilities") else {})
    def close(self): self.closed = True


class ClientTests(unittest.TestCase):
    def test_login_read_add_and_close_use_same_session(self):
        session = Session()
        client = CatalogClient("https://erp.example.com", session)
        self.assertEqual(client.login("example", "test-only-password"), {"version": 1})
        client.search("test", limit=10)
        client.read("a" * 32)
        client.add({"source": "example"})
        client.close()
        self.assertTrue(session.closed)
        self.assertTrue(all(call[2]["allow_redirects"] is False for call in session.calls))
        self.assertFalse(hasattr(client, "password"))
        self.assertEqual(session.calls[2][2]["params"]["limit"], 10)

    def test_rejects_credential_urls_and_remote_plaintext(self):
        for url in ["http://example.com", "https://user:password@example.com", "https://example.com/?token=x"]:
            with self.assertRaises(ValueError): CatalogClient(url)

    def test_unknown_write_does_not_automatically_retry(self):
        import requests
        session = Session()
        def fail(*args, **kwargs):
            session.calls.append(1)
            raise requests.Timeout("secret response text")
        session.request = fail
        with self.assertRaises(RuntimeError) as error:
            CatalogClient("https://erp.example.com", session).add({})
        self.assertEqual(len(session.calls), 1)
        self.assertNotIn("secret", str(error.exception))

    def test_conversion_requires_success_and_preserves_unknown_cost(self):
        document = {"submitted": True, "item": {"name": "Example", "offer_id": "demo", "weight": 1,
                    "weight_unit": "kg", "price": "999"},
                    "import_result": {"result": {"items": [{"offer_id": "demo", "status": "imported"}]}}}
        converted = from_ozon_submission(document, "example-shop")
        self.assertEqual(converted["variants"][0]["weight_grams"], 1000)
        self.assertNotIn("purchase_price_cny", converted["variants"][0])
        self.assertEqual(converted, from_ozon_submission(document, "example-shop"))
        document["submitted"] = False
        with self.assertRaises(ValueError): from_ozon_submission(document, "example-shop")

    def test_schema_only_contains_exchange_and_auth_endpoints(self):
        document = json.loads((Path(__file__).resolve().parents[1] / "openapi.json").read_text(encoding="utf-8"))
        self.assertEqual(len(document["paths"]), 5)
        for path in document["paths"]:
            self.assertTrue("/shared-catalog/v1/" in path or path in {"/api/v1/auth/login", "/api/v1/auth/logout"})


if __name__ == "__main__":
    unittest.main()
