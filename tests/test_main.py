"""Tests for command-line input handling."""

from unittest import TestCase
from unittest.mock import Mock, patch

from repair_assistant.config import AppConfig
from repair_assistant.main import InputValidationError, main, validate_problem


class ValidateProblemTests(TestCase):
    def test_strips_surrounding_whitespace(self) -> None:
        self.assertEqual(validate_problem("  冰箱不冷  "), "冰箱不冷")

    def test_rejects_blank_problem(self) -> None:
        with self.assertRaisesRegex(InputValidationError, "不可為空"):
            validate_problem(" \t\n ")


class MainTests(TestCase):
    def test_runs_analysis_for_user_input(self) -> None:
        config = AppConfig(
            api_key="test-key",
            base_url="https://example.test/v1",
            model="test-model",
        )
        chain = Mock()
        chain.invoke.return_value = "問題摘要\n- 測試結果"

        with (
            patch("repair_assistant.main.load_config", return_value=config),
            patch("builtins.input", return_value="  冰箱不冷  "),
            patch(
                "repair_assistant.main.create_repair_analysis_chain",
                return_value=chain,
            ) as create_chain_mock,
            patch("builtins.print") as print_mock,
        ):
            main()

        create_chain_mock.assert_called_once_with(config)
        chain.invoke.assert_called_once_with({"problem": "冰箱不冷"})
        print_mock.assert_called_once_with("問題摘要\n- 測試結果")
