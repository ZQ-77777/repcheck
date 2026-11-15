"""Live mode against a local fake API server: request format, errors, and answer caching."""
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from helpers import CACHE, E1
from repcheck.llm.base import LLMError
from repcheck.llm.cache import CachingProvider, MockProvider
from repcheck.llm.openai_compat import OpenAICompatibleProvider
from repcheck.pipeline import load_paper, run_spec
from repcheck.schemas import ExtractionStatus

SPEC_REPLY = json.loads((CACHE / "spec_b53ba8a0182a_table3_regression_v1.json").read_text(encoding="utf-8"))["response"]


class FakeAPI(BaseHTTPRequestHandler):
    requests = []
    status = 200
    reject_temperature = False

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeAPI.requests.append({"path": self.path, "auth": self.headers.get("Authorization"),
                                 "api_key": self.headers.get("api-key"), "body": body})
        if FakeAPI.reject_temperature and "temperature" in body:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Unsupported value: temperature does not support 0"}')
            return
        if FakeAPI.status != 200:
            self.send_response(FakeAPI.status)
            self.end_headers()
            self.wfile.write(b'{"error": "invalid api key"}')
            return
        payload = json.dumps({"choices": [{"message": {"content": SPEC_REPLY}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


class LiveProviderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["NO_PROXY"] = os.environ["no_proxy"] = "127.0.0.1,localhost"
        cls.server = HTTPServer(("127.0.0.1", 0), FakeAPI)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        FakeAPI.requests.clear()
        FakeAPI.status = 200
        FakeAPI.reject_temperature = False

    def test_request_format(self):
        p = OpenAICompatibleProvider("sk-test", self.url, "some-model")
        self.assertIn('"fields"', p.complete("system text", "user text"))
        req = FakeAPI.requests[0]
        self.assertEqual(req["path"], "/v1/chat/completions")
        self.assertEqual(req["auth"], "Bearer sk-test")
        self.assertEqual(req["api_key"], "sk-test")              # HKUST GenAI gateway header
        self.assertEqual(req["body"]["model"], "some-model")
        self.assertEqual(req["body"]["temperature"], 0.0)
        self.assertEqual([m["role"] for m in req["body"]["messages"]], ["system", "user"])

    def test_retries_without_temperature_when_model_rejects_it(self):
        FakeAPI.reject_temperature = True
        p = OpenAICompatibleProvider("sk-test", self.url, "gpt-5-mini")
        self.assertIn('"fields"', p.complete("s", "u"))
        self.assertEqual(len(FakeAPI.requests), 2)
        self.assertNotIn("temperature", FakeAPI.requests[1]["body"])

    def test_http_error_is_reported(self):
        FakeAPI.status = 401
        with self.assertRaises(LLMError) as ctx:
            OpenAICompatibleProvider("bad", self.url, "m").complete("s", "u")
        self.assertIn("401", str(ctx.exception))

    def test_missing_key_is_reported(self):
        with self.assertRaises(LLMError):
            OpenAICompatibleProvider("", self.url, "m")

    def test_live_run_is_cached_then_replayed_offline(self):
        with tempfile.TemporaryDirectory() as d:
            live = CachingProvider(OpenAICompatibleProvider("sk-test", self.url, "m"), d)
            c1 = run_spec(load_paper(E1), "Table 3", live)
            self.assertEqual(len(FakeAPI.requests), 1)
            c2 = run_spec(load_paper(E1), "Table 3", live)          # served from the cache
            self.assertEqual(len(FakeAPI.requests), 1)
            c3 = run_spec(load_paper(E1), "Table 3", MockProvider(d))  # offline replay
            for c in (c1, c2, c3):
                self.assertEqual(c.get("sample_period").extraction_status, ExtractionStatus.VERIFIED)


if __name__ == "__main__":
    unittest.main()
