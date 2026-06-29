"""Tests for the repair analysis LCEL chain."""

from unittest import TestCase
from unittest.mock import Mock, patch

from langchain_core.runnables import RunnableLambda

from repair_assistant.chains import (
    RepairAnalysisError,
    analyze_repair_problem,
    create_repair_analysis_chain,
)
from repair_assistant.config import AppConfig
from repair_assistant.schemas import RepairAnalysis


class RepairAnalysisChainTests(TestCase):
    def setUp(self) -> None:
        self.analysis = RepairAnalysis(
            summary="馬達啟動後發出異音。",
            possible_causes=["可能原因一", "可能原因二", "可能原因三"],
            check_steps=["檢查步驟一", "檢查步驟二", "檢查步驟三"],
            questions=["補問一", "補問二", "補問三"],
            priority_steps=["優先一", "優先二", "優先三"],
        )

    def test_builds_lcel_chain_with_structured_output(self) -> None:
        captured_prompts = []
        structured_model = RunnableLambda(
            lambda prompt: captured_prompts.append(prompt) or self.analysis
        )
        fake_model = Mock()
        fake_model.with_structured_output.return_value = structured_model
        config = AppConfig(
            api_key="test-key",
            base_url="https://example.test/v1",
            model="test-model",
        )

        with patch(
            "repair_assistant.chains.ChatOpenAI",
            return_value=fake_model,
        ) as chat_openai_mock:
            chain = create_repair_analysis_chain(config)
            result = chain.invoke({"problem": "馬達啟動後發出異音"})

        chat_openai_mock.assert_called_once_with(
            model="test-model",
            base_url="https://example.test/v1",
            api_key="test-key",
            temperature=0,
        )
        fake_model.with_structured_output.assert_called_once_with(
            RepairAnalysis,
            method="json_mode",
        )
        self.assertIs(result, self.analysis)

        rendered_prompt = "\n".join(
            message.content for message in captured_prompts[0].to_messages()
        )
        self.assertIn("馬達啟動後發出異音", rendered_prompt)
        self.assertIn("可能", rendered_prompt)
        self.assertIn("至少提供 3 筆", rendered_prompt)
        self.assertIn('"priority_steps"', rendered_prompt)

    def test_analyze_repair_problem_returns_repair_analysis(self) -> None:
        chain = Mock()
        chain.invoke.return_value = self.analysis

        with (
            patch("repair_assistant.chains.load_config") as load_config_mock,
            patch(
                "repair_assistant.chains.create_repair_analysis_chain",
                return_value=chain,
            ) as create_chain_mock,
        ):
            result = analyze_repair_problem("馬達有異音")

        create_chain_mock.assert_called_once_with(load_config_mock.return_value)
        chain.invoke.assert_called_once_with({"problem": "馬達有異音"})
        self.assertIs(result, self.analysis)

    def test_analyze_repair_problem_rejects_unstructured_result(self) -> None:
        chain = Mock()
        chain.invoke.return_value = {"summary": "不是 Pydantic 物件"}

        with (
            patch("repair_assistant.chains.load_config"),
            patch(
                "repair_assistant.chains.create_repair_analysis_chain",
                return_value=chain,
            ),
            self.assertRaisesRegex(RepairAnalysisError, "RepairAnalysis"),
        ):
            analyze_repair_problem("馬達有異音")
