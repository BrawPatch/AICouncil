"""Tests for MultiAgentCouncil/llm_client.py. No Ollama needed: urlopen is mocked."""
import json
import os
import unittest
import urllib.error
from unittest import mock

import _paths  # noqa: F401
import llm_client


class FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_urlopen(captured: dict, reply: str = "ok"):
    def _open(req, timeout=None):
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        captured["timeout"] = timeout
        captured["url"] = req.full_url
        return FakeResponse(json.dumps({"response": reply}).encode("utf-8"))

    return _open


class QueryLocalLlmTest(unittest.TestCase):
    def setUp(self):
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop(llm_client.KEEP_ALIVE_ENV, None)

    def call(self, *args, reply="ok", **kwargs):
        captured = {}
        with mock.patch.object(llm_client.urllib.request, "urlopen", fake_urlopen(captured, reply)):
            result = llm_client.query_local_llm(*args, **kwargs)
        return result, captured

    # --- context window -------------------------------------------------------------------
    def test_every_call_sends_num_ctx_of_at_least_8192(self):
        _, sent = self.call("m", "p")
        self.assertGreaterEqual(sent["payload"]["options"]["num_ctx"], 8192)

    def test_larger_num_ctx_is_passed_through(self):
        _, sent = self.call("m", "p", num_ctx=16384)
        self.assertEqual(sent["payload"]["options"]["num_ctx"], 16384)

    def test_num_ctx_below_the_floor_is_rejected_before_any_request(self):
        with mock.patch.object(llm_client.urllib.request, "urlopen") as urlopen:
            with self.assertRaises(ValueError):
                llm_client.query_local_llm("m", "p", num_ctx=4096)
        urlopen.assert_not_called()

    def test_temperature_defaults_to_low_value(self):
        _, sent = self.call("m", "p")
        self.assertEqual(sent["payload"]["options"]["temperature"], 0.2)

    def test_temperature_can_be_overridden(self):
        _, sent = self.call("m", "p", temperature=0.7)
        self.assertEqual(sent["payload"]["options"]["temperature"], 0.7)

    # --- keep-alive -----------------------------------------------------------------------
    def test_keep_alive_defaults_to_unload_immediately(self):
        _, sent = self.call("m", "p")
        self.assertEqual(sent["payload"]["keep_alive"], 0)

    def test_keep_alive_duration_from_environment(self):
        os.environ[llm_client.KEEP_ALIVE_ENV] = "10m"
        _, sent = self.call("m", "p")
        self.assertEqual(sent["payload"]["keep_alive"], "10m")

    def test_keep_alive_compound_duration_from_environment(self):
        os.environ[llm_client.KEEP_ALIVE_ENV] = "1h30m"
        _, sent = self.call("m", "p")
        self.assertEqual(sent["payload"]["keep_alive"], "1h30m")

    def test_keep_alive_integer_seconds_from_environment_is_sent_as_a_number(self):
        os.environ[llm_client.KEEP_ALIVE_ENV] = "300"
        _, sent = self.call("m", "p")
        self.assertEqual(sent["payload"]["keep_alive"], 300)

    def test_keep_alive_minus_one_keeps_the_model_loaded(self):
        os.environ[llm_client.KEEP_ALIVE_ENV] = "-1"
        _, sent = self.call("m", "p")
        self.assertEqual(sent["payload"]["keep_alive"], -1)

    def test_blank_keep_alive_falls_back_to_default(self):
        os.environ[llm_client.KEEP_ALIVE_ENV] = "   "
        _, sent = self.call("m", "p")
        self.assertEqual(sent["payload"]["keep_alive"], 0)

    def test_invalid_keep_alive_is_rejected_before_any_request(self):
        os.environ[llm_client.KEEP_ALIVE_ENV] = "banana"
        with mock.patch.object(llm_client.urllib.request, "urlopen") as urlopen:
            with self.assertRaises(ValueError) as ctx:
                llm_client.query_local_llm("m", "p")
        self.assertIn(llm_client.KEEP_ALIVE_ENV, str(ctx.exception))
        urlopen.assert_not_called()

    # --- request shape and errors -----------------------------------------------------------
    def test_request_carries_model_prompt_and_disables_streaming(self):
        _, sent = self.call("qwen2.5-coder:7b", "write tests")
        self.assertEqual(sent["payload"]["model"], "qwen2.5-coder:7b")
        self.assertEqual(sent["payload"]["prompt"], "write tests")
        self.assertIs(sent["payload"]["stream"], False)
        self.assertEqual(sent["url"], llm_client.OLLAMA_URL)

    def test_returns_the_response_text(self):
        result, _ = self.call("m", "p", reply="hello there")
        self.assertEqual(result, "hello there")

    def test_timeout_is_forwarded(self):
        _, sent = self.call("m", "p", timeout=42)
        self.assertEqual(sent["timeout"], 42)

    def test_positional_timeout_still_works(self):
        # Existing callers may pass the timeout as the third positional argument.
        _, sent = self.call("m", "p", 99)
        self.assertEqual(sent["timeout"], 99)

    def test_network_errors_become_runtime_errors_naming_the_model(self):
        boom = urllib.error.URLError("connection refused")
        with mock.patch.object(llm_client.urllib.request, "urlopen", side_effect=boom):
            with self.assertRaises(RuntimeError) as ctx:
                llm_client.query_local_llm("mistral:7b", "p")
        self.assertIn("mistral:7b", str(ctx.exception))

    def test_reply_without_response_field_becomes_a_runtime_error(self):
        class NoResponse(FakeResponse):
            pass

        def _open(req, timeout=None):
            return NoResponse(json.dumps({"error": "model not found"}).encode("utf-8"))

        with mock.patch.object(llm_client.urllib.request, "urlopen", _open):
            with self.assertRaises(RuntimeError):
                llm_client.query_local_llm("m", "p")


if __name__ == "__main__":
    unittest.main()
