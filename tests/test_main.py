"""Tests for command-line input handling."""

from unittest import TestCase
from unittest.mock import patch

from repair_assistant.chains import RepairAnalysisError
from repair_assistant.main import (
    InputValidationError,
    format_repair_analysis,
    main,
    validate_problem,
)
from repair_assistant.schemas import RepairAnalysis


class ValidateProblemTests(TestCase):
    def test_strips_surrounding_whitespace(self) -> None:
        self.assertEqual(validate_problem("  冰箱不冷  "), "冰箱不冷")

    def test_rejects_blank_problem(self) -> None:
        with self.assertRaisesRegex(
            InputValidationError,
            "請輸入故障描述，不可為空。",
        ):
            validate_problem(" \t\n ")


class FormatRepairAnalysisTests(TestCase):
    def setUp(self) -> None:
        self.analysis = RepairAnalysis(
            summary="印表機在出紙口附近卡紙。",
            possible_causes=["可能原因一", "可能原因二", "可能原因三"],
            check_steps=["檢查步驟一", "檢查步驟二", "檢查步驟三"],
            questions=["補問一", "補問二", "補問三"],
            priority_steps=["優先一", "優先二", "優先三"],
        )

    def test_contains_required_headings_and_numbered_lists(self) -> None:
        result = format_repair_analysis(self.analysis)

        for heading in (
            "## 問題摘要",
            "## 可能原因",
            "## 初步檢查方向",
            "## 需要補問的資訊",
            "## 建議處理優先順序",
        ):
            self.assertIn(heading, result)
        self.assertGreaterEqual(result.count("1. "), 4)
        self.assertGreaterEqual(result.count("2. "), 4)
        self.assertGreaterEqual(result.count("3. "), 4)


class MainTests(TestCase):
    def test_formats_and_prints_structured_analysis(self) -> None:
        analysis = RepairAnalysis(
            summary="印表機在出紙口附近卡紙。",
            possible_causes=["可能原因一", "可能原因二", "可能原因三"],
            check_steps=["檢查步驟一", "檢查步驟二", "檢查步驟三"],
            questions=["補問一", "補問二", "補問三"],
            priority_steps=["優先一", "優先二", "優先三"],
        )

        with (
            patch("builtins.input", return_value="  冰箱不冷  "),
            patch(
                "repair_assistant.main.analyze_repair_problem",
                return_value=analysis,
            ) as analyze_mock,
            patch("builtins.print") as print_mock,
        ):
            main()

        analyze_mock.assert_called_once_with("冰箱不冷")
        output = print_mock.call_args.args[0]
        self.assertIn("## 問題摘要", output)
        self.assertIn("1. 可能原因一", output)

    def test_reports_structured_output_error_clearly(self) -> None:
        error_message = "模型回覆無法解析為 RepairAnalysis 結構化格式。"

        with (
            patch("builtins.input", return_value="印表機卡紙"),
            patch(
                "repair_assistant.main.analyze_repair_problem",
                side_effect=RepairAnalysisError(error_message),
            ),
            self.assertRaisesRegex(SystemExit, f"錯誤：{error_message}"),
        ):
            main()
