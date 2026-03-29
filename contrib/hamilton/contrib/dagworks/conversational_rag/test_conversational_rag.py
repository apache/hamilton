# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Tests for the conversational_rag dataflow with multi-provider support."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(
    0,
    os.path.dirname(os.path.abspath(__file__)),
)

import openai

from hamilton import driver

from hamilton.contrib.dagworks import conversational_rag


# ──────────────────────────── Unit Tests ────────────────────────────


class TestStandaloneQuestionPrompt:
    """Tests for standalone_question_prompt (provider-independent)."""

    def test_includes_chat_history(self):
        result = conversational_rag.standalone_question_prompt(
            chat_history=["Human: Hi", "AI: Hello"],
            question="Where did he work?",
        )
        assert "Human: Hi" in result
        assert "AI: Hello" in result

    def test_includes_question(self):
        result = conversational_rag.standalone_question_prompt(
            chat_history=[],
            question="What is Hamilton?",
        )
        assert "What is Hamilton?" in result

    def test_empty_chat_history(self):
        result = conversational_rag.standalone_question_prompt(
            chat_history=[],
            question="test question",
        )
        assert "test question" in result


class TestAnswerPrompt:
    """Tests for answer_prompt (provider-independent)."""

    def test_includes_context_and_question(self):
        result = conversational_rag.answer_prompt(
            context="Hamilton builds DAGs",
            standalone_question="What is Hamilton?",
        )
        assert "Hamilton builds DAGs" in result
        assert "What is Hamilton?" in result


class TestModelConfig:
    """Tests for model configuration functions."""

    def test_model_openai_returns_gpt35(self):
        assert conversational_rag.model__openai() == "gpt-3.5-turbo"

    def test_model_minimax_returns_m27(self):
        assert conversational_rag.model__minimax() == "MiniMax-M2.7"


class TestOpenAIProvider:
    """Tests for OpenAI provider configuration."""

    def test_llm_client_openai_returns_client(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = conversational_rag.llm_client__openai()
            assert isinstance(client, openai.OpenAI)

    def test_standalone_question_calls_with_model(self):
        mock_client = MagicMock(spec=openai.OpenAI)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "standalone question"
        mock_client.chat.completions.create.return_value = mock_response

        result = conversational_rag.standalone_question(
            standalone_question_prompt="test prompt",
            llm_client=mock_client,
            model="gpt-3.5-turbo",
        )
        assert result == "standalone question"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test prompt"}],
        )

    def test_rag_response_calls_with_model(self):
        mock_client = MagicMock(spec=openai.OpenAI)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Stitch Fix"
        mock_client.chat.completions.create.return_value = mock_response

        result = conversational_rag.conversational_rag_response(
            answer_prompt="Where did stefan work?",
            llm_client=mock_client,
            model="gpt-3.5-turbo",
        )
        assert result == "Stitch Fix"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Where did stefan work?"}],
        )


class TestMiniMaxProvider:
    """Tests for MiniMax provider configuration."""

    def test_llm_client_minimax_base_url(self):
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}):
            client = conversational_rag.llm_client__minimax()
            assert isinstance(client, openai.OpenAI)
            assert str(client.base_url).rstrip("/") == "https://api.minimax.io/v1"

    def test_llm_client_minimax_api_key(self):
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "my-key"}):
            client = conversational_rag.llm_client__minimax()
            assert client.api_key == "my-key"

    def test_standalone_question_with_minimax_model(self):
        mock_client = MagicMock(spec=openai.OpenAI)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "standalone question"
        mock_client.chat.completions.create.return_value = mock_response

        result = conversational_rag.standalone_question(
            standalone_question_prompt="test prompt",
            llm_client=mock_client,
            model="MiniMax-M2.7",
        )
        assert result == "standalone question"
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "MiniMax-M2.7"

    def test_rag_response_with_minimax_model(self):
        mock_client = MagicMock(spec=openai.OpenAI)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "MiniMax answer"
        mock_client.chat.completions.create.return_value = mock_response

        result = conversational_rag.conversational_rag_response(
            answer_prompt="Where did stefan work?",
            llm_client=mock_client,
            model="MiniMax-M2.7",
        )
        assert result == "MiniMax answer"
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "MiniMax-M2.7"


class TestHamiltonDriverConfig:
    """Tests for Hamilton driver configuration."""

    def test_driver_builds_with_default_config(self):
        dr = driver.Builder().with_modules(conversational_rag).with_config({}).build()
        assert dr is not None

    def test_driver_builds_with_openai_config(self):
        dr = (
            driver.Builder()
            .with_modules(conversational_rag)
            .with_config({"provider": "openai"})
            .build()
        )
        assert dr is not None

    def test_driver_builds_with_minimax_config(self):
        dr = (
            driver.Builder()
            .with_modules(conversational_rag)
            .with_config({"provider": "minimax"})
            .build()
        )
        assert dr is not None

    def test_default_config_has_required_nodes(self):
        dr = driver.Builder().with_modules(conversational_rag).with_config({}).build()
        graph_nodes = {n.name for n in dr.graph.get_nodes()}
        assert "llm_client" in graph_nodes
        assert "model" in graph_nodes
        assert "standalone_question" in graph_nodes
        assert "conversational_rag_response" in graph_nodes

    def test_minimax_config_has_required_nodes(self):
        dr = (
            driver.Builder()
            .with_modules(conversational_rag)
            .with_config({"provider": "minimax"})
            .build()
        )
        graph_nodes = {n.name for n in dr.graph.get_nodes()}
        assert "llm_client" in graph_nodes
        assert "model" in graph_nodes
        assert "standalone_question" in graph_nodes
        assert "conversational_rag_response" in graph_nodes

    def test_default_config_end_to_end_mocked(self):
        """Test end-to-end with mocked OpenAI client."""
        mock_client = MagicMock(spec=openai.OpenAI)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Stitch Fix"
        mock_client.chat.completions.create.return_value = mock_response

        dr = driver.Builder().with_modules(conversational_rag).with_config({}).build()
        result = dr.execute(
            ["conversational_rag_response"],
            overrides={
                "llm_client": mock_client,
                "standalone_question": "Where did Stefan work?",
                "answer_prompt": "Context: Stefan worked at Stitch Fix\n\nQuestion: Where did Stefan work?",
            },
        )
        assert result["conversational_rag_response"] == "Stitch Fix"

    def test_minimax_config_end_to_end_mocked(self):
        """Test end-to-end with mocked MiniMax client."""
        mock_client = MagicMock(spec=openai.OpenAI)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "MiniMax answer"
        mock_client.chat.completions.create.return_value = mock_response

        dr = (
            driver.Builder()
            .with_modules(conversational_rag)
            .with_config({"provider": "minimax"})
            .build()
        )
        result = dr.execute(
            ["conversational_rag_response"],
            overrides={
                "llm_client": mock_client,
                "standalone_question": "Where did Stefan work?",
                "answer_prompt": "Context: Stefan worked at Stitch Fix\n\nQuestion: Where did Stefan work?",
            },
        )
        assert result["conversational_rag_response"] == "MiniMax answer"


# ──────────────────────── Integration Tests ─────────────────────────


class TestMiniMaxIntegration:
    """Integration tests that call the real MiniMax API."""

    @pytest.fixture
    def minimax_api_key(self):
        key = os.environ.get("MINIMAX_API_KEY")
        if not key:
            pytest.skip("MINIMAX_API_KEY not set")
        return key

    def test_minimax_client_creation(self, minimax_api_key):
        with patch.dict(os.environ, {"MINIMAX_API_KEY": minimax_api_key}):
            client = conversational_rag.llm_client__minimax()
            assert isinstance(client, openai.OpenAI)

    def test_minimax_standalone_question_real_api(self, minimax_api_key):
        with patch.dict(os.environ, {"MINIMAX_API_KEY": minimax_api_key}):
            client = conversational_rag.llm_client__minimax()
            result = conversational_rag.standalone_question(
                standalone_question_prompt="Given the following conversation:\n"
                "Human: Who wrote this example?\nAI: Stefan\n"
                "Follow Up Input: Where did he work?\n"
                "Standalone question:",
                llm_client=client,
                model="MiniMax-M2.7",
            )
            assert isinstance(result, str)
            assert len(result) > 0

    def test_minimax_conversational_rag_response_real_api(self, minimax_api_key):
        with patch.dict(os.environ, {"MINIMAX_API_KEY": minimax_api_key}):
            client = conversational_rag.llm_client__minimax()
            result = conversational_rag.conversational_rag_response(
                answer_prompt="Answer the question based only on the following context:\n"
                "Stefan worked at Stitch Fix.\n\n"
                "Question: Where did Stefan work?",
                llm_client=client,
                model="MiniMax-M2.7",
            )
            assert isinstance(result, str)
            assert len(result) > 0
