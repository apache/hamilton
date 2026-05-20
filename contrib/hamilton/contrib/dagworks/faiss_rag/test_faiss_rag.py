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

"""Tests for the faiss_rag dataflow with multi-provider support."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add the parent directory to allow importing the module
sys.path.insert(
    0,
    os.path.dirname(os.path.abspath(__file__)),
)

import openai

from hamilton import driver

# Import the module under test
from hamilton.contrib.dagworks import faiss_rag

# ──────────────────────────── Unit Tests ────────────────────────────


class TestRagPrompt:
    """Tests for the rag_prompt function (provider-independent)."""

    def test_rag_prompt_includes_context(self):
        result = faiss_rag.rag_prompt(
            context="Hamilton is a DAG framework", question="What is Hamilton?"
        )
        assert "Hamilton is a DAG framework" in result

    def test_rag_prompt_includes_question(self):
        result = faiss_rag.rag_prompt(context="some context", question="What is Hamilton?")
        assert "What is Hamilton?" in result

    def test_rag_prompt_format(self):
        result = faiss_rag.rag_prompt(context="ctx", question="q")
        assert "Answer the question" in result
        assert "ctx" in result
        assert "q" in result


class TestModelConfig:
    """Tests for model configuration functions."""

    def test_model_openai_returns_gpt35(self):
        assert faiss_rag.model__openai() == "gpt-3.5-turbo"

    def test_model_minimax_returns_m27(self):
        assert faiss_rag.model__minimax() == "MiniMax-M2.7"


class TestOpenAIProvider:
    """Tests for OpenAI provider configuration."""

    def test_llm_client_openai_returns_openai_client(self):
        """Test that the OpenAI client is correctly created."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = faiss_rag.llm_client__openai()
            assert isinstance(client, openai.OpenAI)

    def test_rag_response_calls_with_model(self):
        """Test that rag_response calls chat completions with the given model."""
        mock_client = MagicMock(spec=openai.OpenAI)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Stitch Fix"
        mock_client.chat.completions.create.return_value = mock_response

        result = faiss_rag.rag_response(
            rag_prompt="Where did stefan work?",
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

    def test_llm_client_minimax_returns_openai_client_with_minimax_base_url(self):
        """Test that the MiniMax client uses the correct base_url."""
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-minimax-key"}):
            client = faiss_rag.llm_client__minimax()
            assert isinstance(client, openai.OpenAI)
            assert "minimax" in str(client.base_url).lower()

    def test_llm_client_minimax_uses_env_api_key(self):
        """Test that the MiniMax client reads MINIMAX_API_KEY from env."""
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "my-secret-key"}):
            client = faiss_rag.llm_client__minimax()
            assert client.api_key == "my-secret-key"

    def test_rag_response_with_minimax_model(self):
        """Test that rag_response works with MiniMax-M2.7 model."""
        mock_client = MagicMock(spec=openai.OpenAI)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Stitch Fix"
        mock_client.chat.completions.create.return_value = mock_response

        result = faiss_rag.rag_response(
            rag_prompt="Where did stefan work?",
            llm_client=mock_client,
            model="MiniMax-M2.7",
        )

        assert result == "Stitch Fix"
        mock_client.chat.completions.create.assert_called_once_with(
            model="MiniMax-M2.7",
            messages=[{"role": "user", "content": "Where did stefan work?"}],
        )


class TestHamiltonDriverConfig:
    """Tests for Hamilton driver configuration with providers."""

    def test_driver_builds_with_default_config(self):
        """Test that the driver builds successfully with default (empty) config."""
        dr = driver.Builder().with_modules(faiss_rag).with_config({}).build()
        assert dr is not None

    def test_driver_builds_with_openai_config(self):
        """Test that the driver builds successfully with explicit OpenAI config."""
        dr = driver.Builder().with_modules(faiss_rag).with_config({"provider": "openai"}).build()
        assert dr is not None

    def test_driver_builds_with_minimax_config(self):
        """Test that the driver builds successfully with MiniMax config."""
        dr = driver.Builder().with_modules(faiss_rag).with_config({"provider": "minimax"}).build()
        assert dr is not None

    def test_default_config_includes_required_nodes(self):
        """Test that default config resolves to all required nodes."""
        dr = driver.Builder().with_modules(faiss_rag).with_config({}).build()
        graph_nodes = {n.name for n in dr.graph.get_nodes()}
        assert "llm_client" in graph_nodes
        assert "model" in graph_nodes
        assert "rag_response" in graph_nodes

    def test_minimax_config_includes_required_nodes(self):
        """Test that minimax config resolves to all required nodes."""
        dr = driver.Builder().with_modules(faiss_rag).with_config({"provider": "minimax"}).build()
        graph_nodes = {n.name for n in dr.graph.get_nodes()}
        assert "llm_client" in graph_nodes
        assert "model" in graph_nodes
        assert "rag_response" in graph_nodes

    def test_default_config_executes_rag(self):
        """Test end-to-end execution with default config using mocked client."""
        mock_client = MagicMock(spec=openai.OpenAI)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Stitch Fix"
        mock_client.chat.completions.create.return_value = mock_response

        dr = driver.Builder().with_modules(faiss_rag).with_config({}).build()
        result = dr.execute(
            ["rag_response"],
            inputs={"rag_prompt": "Where did stefan work?"},
            overrides={"llm_client": mock_client, "rag_prompt": "Where did stefan work?"},
        )
        assert result["rag_response"] == "Stitch Fix"

    def test_minimax_config_executes_rag(self):
        """Test end-to-end execution with MiniMax config using mocked client."""
        mock_client = MagicMock(spec=openai.OpenAI)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "MiniMax response"
        mock_client.chat.completions.create.return_value = mock_response

        dr = driver.Builder().with_modules(faiss_rag).with_config({"provider": "minimax"}).build()
        result = dr.execute(
            ["rag_response"],
            inputs={"rag_prompt": "Where did stefan work?"},
            overrides={"llm_client": mock_client, "rag_prompt": "Where did stefan work?"},
        )
        assert result["rag_response"] == "MiniMax response"


class TestMiniMaxModelConstants:
    """Tests for MiniMax model configuration constants."""

    def test_minimax_base_url(self):
        """Test that MiniMax base URL is correct."""
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}):
            client = faiss_rag.llm_client__minimax()
            assert str(client.base_url).rstrip("/") == "https://api.minimax.io/v1"


# ──────────────────────── Integration Tests ─────────────────────────


class TestMiniMaxIntegration:
    """Integration tests that call the real MiniMax API."""

    @pytest.fixture
    def minimax_api_key(self):
        """Get MiniMax API key from environment."""
        key = os.environ.get("MINIMAX_API_KEY")
        if not key:
            pytest.skip("MINIMAX_API_KEY not set")
        return key

    def test_minimax_client_creation(self, minimax_api_key):
        """Test creating a real MiniMax client."""
        with patch.dict(os.environ, {"MINIMAX_API_KEY": minimax_api_key}):
            client = faiss_rag.llm_client__minimax()
            assert isinstance(client, openai.OpenAI)
            assert client.api_key == minimax_api_key

    def test_minimax_rag_response_real_api(self, minimax_api_key):
        """Test a real RAG response from MiniMax API."""
        with patch.dict(os.environ, {"MINIMAX_API_KEY": minimax_api_key}):
            client = faiss_rag.llm_client__minimax()
            result = faiss_rag.rag_response(
                rag_prompt="Answer the question based only on the following context:\n"
                "Stefan worked at Stitch Fix.\n\n"
                "Question: Where did Stefan work?",
                llm_client=client,
                model="MiniMax-M2.7",
            )
            assert isinstance(result, str)
            assert len(result) > 0

    def test_minimax_driver_execution(self, minimax_api_key):
        """Test Hamilton driver execution with MiniMax config."""
        with patch.dict(os.environ, {"MINIMAX_API_KEY": minimax_api_key}):
            dr = (
                driver.Builder()
                .with_modules(faiss_rag)
                .with_config({"provider": "minimax"})
                .build()
            )

            client = faiss_rag.llm_client__minimax()
            result = dr.execute(
                ["rag_response"],
                overrides={
                    "llm_client": client,
                    "rag_prompt": "Answer the question based only on the following context:\n"
                    "Hamilton is a Python library for DAGs.\n\n"
                    "Question: What is Hamilton?",
                },
            )
            assert "rag_response" in result
            assert isinstance(result["rag_response"], str)
            assert len(result["rag_response"]) > 0
