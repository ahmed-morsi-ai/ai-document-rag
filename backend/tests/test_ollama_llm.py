import unittest
from unittest.mock import Mock, patch

import httpx

from app.services.llm import LLMProvider, OllamaLLMProvider


class OllamaLLMProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = OllamaLLMProvider(
            base_url="http://localhost:11434/",
            model_name="test-model",
            timeout=42.0,
        )

    def test_implements_llm_provider(self):
        self.assertIsInstance(self.provider, LLMProvider)

    def test_generate_returns_plain_text_and_sends_expected_request(self):
        response = Mock()
        response.json.return_value = {
            "model": "test-model",
            "response": "generated answer",
            "done": True,
        }

        with patch(
            "app.services.llm.ollama.httpx.post",
            return_value=response,
        ) as post:
            result = self.provider.generate("hello")

        response.raise_for_status.assert_called_once_with()
        post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "test-model",
                "prompt": "hello",
                "stream": False,
            },
            timeout=42.0,
        )
        self.assertEqual(result, "generated answer")
        self.assertIsInstance(result, str)

    def test_prompt_is_passed_unchanged(self):
        response = Mock()
        response.json.return_value = {
            "response": "answer",
        }

        prompt = "  preserve whitespace  "

        with patch(
            "app.services.llm.ollama.httpx.post",
            return_value=response,
        ) as post:
            self.provider.generate(prompt)

        self.assertEqual(
            post.call_args.kwargs["json"]["prompt"],
            prompt,
        )

    def test_empty_prompt_is_rejected_before_http_call(self):
        with patch(
            "app.services.llm.ollama.httpx.post",
        ) as post:
            with self.assertRaisesRegex(
                ValueError,
                "prompt must not be empty",
            ):
                self.provider.generate("   ")

        post.assert_not_called()

    def test_client_failure_propagates(self):
        with patch(
            "app.services.llm.ollama.httpx.post",
            side_effect=httpx.ConnectError("connection failed"),
        ) as post:
            with self.assertRaises(httpx.ConnectError):
                self.provider.generate("hello")

        post.assert_called_once()

    def test_http_status_failure_propagates(self):
        response = Mock()
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "server error",
            request=Mock(),
            response=Mock(),
        )

        with patch(
            "app.services.llm.ollama.httpx.post",
            return_value=response,
        ):
            with self.assertRaises(httpx.HTTPStatusError):
                self.provider.generate("hello")

    def test_malformed_response_is_rejected(self):
        response = Mock()
        response.json.return_value = {
            "model": "test-model",
            "done": True,
        }

        with patch(
            "app.services.llm.ollama.httpx.post",
            return_value=response,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Ollama response did not contain text",
            ):
                self.provider.generate("hello")

    def test_empty_base_url_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "base_url must not be empty",
        ):
            OllamaLLMProvider(
                base_url="   ",
                model_name="test-model",
                timeout=42.0,
            )

    def test_empty_model_name_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "model_name must not be empty",
        ):
            OllamaLLMProvider(
                base_url="http://localhost:11434",
                model_name="   ",
                timeout=42.0,
            )

    def test_invalid_timeout_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "timeout must be greater than 0",
        ):
            OllamaLLMProvider(
                base_url="http://localhost:11434",
                model_name="test-model",
                timeout=0,
            )


if __name__ == "__main__":
    unittest.main()
