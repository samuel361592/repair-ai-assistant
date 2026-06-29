"""Tests for the repair analysis LCEL chain."""

from unittest import TestCase
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from repair_assistant.chains import (
    FORMAT_FALLBACK,
    OUTPUT_SECTIONS,
    create_repair_analysis_chain,
    ensure_output_format,
)
from repair_assistant.config import AppConfig


class RepairAnalysisChainTests(TestCase):
    def test_builds_lcel_chain_with_required_prompt_and_output_parser(self) -> None:
        captured_prompts = []
        expected_output = "\n".join(f"{section}\n- 測試內容" for section in OUTPUT_SECTIONS)
        fake_model = RunnableLambda(
            lambda prompt: captured_prompts.append(prompt) or expected_output
        )
        config = AppConfig(
            api_key="test-key",
            base_url="https://example.test/v1",
            model="test-model",
        )

        with patch(
            "repair_assistant.chains.ChatOpenAI", return_value=fake_model
        ) as chat_openai_mock:
            chain = create_repair_analysis_chain(config)
            result = chain.invoke({"problem": "馬達啟動後發出異音"})

        chat_openai_mock.assert_called_once_with(
            model="test-model",
            base_url="https://example.test/v1",
            api_key="test-key",
        )
        self.assertEqual(result, expected_output)

        rendered_prompt = "\n".join(
            message.content for message in captured_prompts[0].to_messages()
        )
        self.assertIn("馬達啟動後發出異音", rendered_prompt)
        for section in OUTPUT_SECTIONS:
            self.assertIn(section, rendered_prompt)

    def test_replaces_model_output_that_omits_required_sections(self) -> None:
        result = ensure_output_format("請提供更多設備資訊。")

        self.assertEqual(result, FORMAT_FALLBACK)
        positions = [result.index(section) for section in OUTPUT_SECTIONS]
        self.assertEqual(positions, sorted(positions))
