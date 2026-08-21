import unittest

from app.services.llm import LLMProvider


class FakeLLMProvider(LLMProvider):
    """Deterministic test-only LLM provider."""

    def _generate(self, prompt: str) -> str:
        return f"ANSWER: {prompt}"


class LLMProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = FakeLLMProvider()

    def test_llm_provider_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            LLMProvider()

    def test_fake_provider_satisfies_contract(self):
        result = self.provider.generate("hello")

        self.assertEqual(
            result,
            "ANSWER: hello",
        )
        self.assertIsInstance(result, str)

    def test_same_input_is_deterministic(self):
        first = self.provider.generate("hello")
        second = self.provider.generate("hello")

        self.assertEqual(first, second)

    def test_empty_prompt_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "prompt must not be empty",
        ):
            self.provider.generate("")

    def test_whitespace_prompt_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "prompt must not be empty",
        ):
            self.provider.generate("   ")

    def test_prompt_reaches_fake_provider_unchanged(self):
        prompt = "  preserve whitespace  "

        self.assertEqual(
            self.provider.generate(prompt),
            f"ANSWER: {prompt}",
        )


if __name__ == "__main__":
    unittest.main()
