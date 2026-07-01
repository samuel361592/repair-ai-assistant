"""Tests for application configuration."""

import os
from unittest import TestCase
from unittest.mock import patch

from repair_assistant.config import ConfigurationError, load_config


class LoadConfigTests(TestCase):
    @patch("repair_assistant.config.load_dotenv")
    def test_loads_all_required_values(self, load_dotenv_mock) -> None:
        environment = {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_BASE_URL": "https://example.test/v1",
            "OPENAI_MODEL": "test-model",
        }

        with patch.dict(os.environ, environment, clear=True):
            config = load_config()

        load_dotenv_mock.assert_called_once_with()
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.base_url, "https://example.test/v1")
        self.assertEqual(config.model, "test-model")
        self.assertEqual(config.embedding_model, "text-embedding-3-small")
        self.assertEqual(config.manuals_dir, "data/manuals")
        self.assertEqual(
            config.vectorstore_dir,
            "data/vectorstore/chroma",
        )

    @patch("repair_assistant.config.load_dotenv")
    def test_loads_optional_rag_settings(self, _load_dotenv_mock) -> None:
        environment = {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_BASE_URL": "https://example.test/v1",
            "OPENAI_MODEL": "test-model",
            "OPENAI_EMBEDDING_MODEL": "embedding-model",
            "RAG_MANUALS_DIR": "custom/manuals",
            "RAG_VECTORSTORE_DIR": "custom/vectorstore",
        }

        with patch.dict(os.environ, environment, clear=True):
            config = load_config()

        self.assertEqual(config.embedding_model, "embedding-model")
        self.assertEqual(config.manuals_dir, "custom/manuals")
        self.assertEqual(config.vectorstore_dir, "custom/vectorstore")

    @patch("repair_assistant.config.load_dotenv")
    def test_reports_every_missing_or_blank_value(self, _load_dotenv_mock) -> None:
        environment = {
            "OPENAI_API_KEY": " ",
            "OPENAI_MODEL": "test-model",
        }

        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaises(ConfigurationError) as context:
                load_config()

        message = str(context.exception)
        self.assertIn("OPENAI_API_KEY", message)
        self.assertIn("OPENAI_BASE_URL", message)
        self.assertIn(".env", message)
