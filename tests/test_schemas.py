"""Tests for structured maintenance analysis schemas."""

from unittest import TestCase

from pydantic import ValidationError

from repair_assistant.schemas import RepairAnalysis


class RepairAnalysisSchemaTests(TestCase):
    def setUp(self) -> None:
        self.data = {
            "summary": "印表機在出紙口附近卡紙。",
            "possible_causes": ["原因一", "原因二", "原因三"],
            "check_steps": ["檢查一", "檢查二", "檢查三"],
            "questions": ["問題一", "問題二", "問題三"],
            "priority_steps": ["優先一", "優先二", "優先三"],
        }

    def test_contains_all_required_fields(self) -> None:
        self.assertEqual(
            set(RepairAnalysis.model_fields),
            {
                "summary",
                "possible_causes",
                "check_steps",
                "questions",
                "priority_steps",
            },
        )

    def test_list_fields_are_lists(self) -> None:
        analysis = RepairAnalysis(**self.data)

        self.assertIsInstance(analysis.possible_causes, list)
        self.assertIsInstance(analysis.check_steps, list)
        self.assertIsInstance(analysis.questions, list)
        self.assertIsInstance(analysis.priority_steps, list)

    def test_list_fields_require_at_least_three_items(self) -> None:
        self.data["possible_causes"] = ["原因一", "原因二"]

        with self.assertRaises(ValidationError):
            RepairAnalysis(**self.data)
