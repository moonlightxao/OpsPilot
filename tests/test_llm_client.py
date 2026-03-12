# -*- coding: utf-8 -*-
"""LLM 客户端测试"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock

from src.llm.base import BaseLLMClient, LLMResponse


class TestLLMResponse:
    """LLMResponse 数据类测试"""

    def test_create_response(self):
        """测试创建响应对象"""
        response = LLMResponse(
            content="Hello",
            model="gpt-4o-mini",
            usage={"prompt_tokens": 10, "completion_tokens": 5}
        )
        assert response.content == "Hello"
        assert response.model == "gpt-4o-mini"
        assert response.usage["prompt_tokens"] == 10

    def test_create_response_with_raw(self):
        """测试创建带原始响应的响应对象"""
        raw = {"id": "test-123"}
        response = LLMResponse(
            content="Test",
            model="gpt-4o-mini",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            raw_response=raw
        )
        assert response.raw_response == raw

    def test_create_response_minimal(self):
        """测试创建最小响应对象"""
        response = LLMResponse(
            content="Test",
            model="test-model",
            usage={}
        )
        assert response.content == "Test"
        assert response.usage == {}


class TestBaseLLMClient:
    """BaseLLMClient 抽象基类测试"""

    def test_base_client_cannot_instantiate(self):
        """测试抽象基类不能直接实例化"""
        with pytest.raises(TypeError):
            BaseLLMClient("test-model")

    def test_get_model_info(self):
        """测试获取模型信息"""
        class MockClient(BaseLLMClient):
            def chat(self, system_prompt, user_prompt, **kwargs):
                return LLMResponse(content="test", model="test", usage={})

            def is_available(self):
                return True

        client = MockClient("gpt-4")
        info = client.get_model_info()
        assert info["provider"] == "MockClient"
        assert info["model"] == "gpt-4"


class TestOpenAIClient:
    """OpenAI 客户端测试"""

    def test_create_client_default_params(self):
        """测试使用默认参数创建客户端"""
        mock_openai_module = MagicMock()
        mock_openai_module.OpenAI = MagicMock()
        sys.modules["openai"] = mock_openai_module

        from src.llm.openai_client import OpenAIClient

        client = OpenAIClient(api_key="test-key")
        assert client.model == "gpt-4o-mini"
        mock_openai_module.OpenAI.assert_called_once()

        del sys.modules["openai"]

    def test_create_client_custom_model(self):
        """测试使用自定义模型创建客户端"""
        mock_openai_module = MagicMock()
        mock_openai_module.OpenAI = MagicMock()
        sys.modules["openai"] = mock_openai_module

        from src.llm.openai_client import OpenAIClient

        client = OpenAIClient(api_key="test-key", model="gpt-4")
        assert client.model == "gpt-4"

        del sys.modules["openai"]

    def test_create_client_with_base_url(self):
        """测试使用自定义 base_url 创建客户端"""
        mock_openai_module = MagicMock()
        mock_openai_module.OpenAI = MagicMock()
        sys.modules["openai"] = mock_openai_module

        from src.llm.openai_client import OpenAIClient

        client = OpenAIClient(
            api_key="test-key",
            base_url="https://api.example.com"
        )
        mock_openai_module.OpenAI.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.example.com"
        )

        del sys.modules["openai"]

    def test_chat(self):
        """测试聊天功能"""
        mock_openai_module = MagicMock()
        mock_openai_class = MagicMock()
        sys.modules["openai"] = mock_openai_module
        mock_openai_module.OpenAI = mock_openai_class

        from src.llm.openai_client import OpenAIClient

        # Mock 响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.model_dump.return_value = {}

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        client = OpenAIClient(api_key="test-key")
        response = client.chat("system", "user")

        assert response.content == "Test response"
        assert response.model == "gpt-4o-mini"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 5

        del sys.modules["openai"]

    def test_chat_with_custom_params(self):
        """测试使用自定义参数聊天"""
        mock_openai_module = MagicMock()
        mock_openai_class = MagicMock()
        sys.modules["openai"] = mock_openai_module
        mock_openai_module.OpenAI = mock_openai_class

        from src.llm.openai_client import OpenAIClient

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.model = "gpt-4o-mini"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 3
        mock_response.model_dump.return_value = {}

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        client = OpenAIClient(api_key="test-key")
        response = client.chat("system", "user", max_tokens=1000, temperature=0.5)

        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["max_tokens"] == 1000
        assert call_args.kwargs["temperature"] == 0.5

        del sys.modules["openai"]

    def test_is_available_with_key(self):
        """测试有 API Key 时可用性检查"""
        mock_openai_module = MagicMock()
        sys.modules["openai"] = mock_openai_module
        mock_openai_module.OpenAI = MagicMock()

        from src.llm.openai_client import OpenAIClient

        client = OpenAIClient(api_key="test-key")
        assert client.is_available() is True

        del sys.modules["openai"]

    def test_is_available_without_key(self):
        """测试无 API Key 时可用性检查"""
        mock_openai_module = MagicMock()
        sys.modules["openai"] = mock_openai_module
        mock_openai_module.OpenAI = MagicMock()

        from src.llm.openai_client import OpenAIClient

        with patch.dict("os.environ", {}, clear=True):
            client = OpenAIClient(api_key=None)
            assert client.is_available() is False

        del sys.modules["openai"]


class TestAnthropicClient:
    """Anthropic 客户端测试"""

    def test_create_client_default_params(self):
        """测试使用默认参数创建客户端"""
        mock_anthropic_module = MagicMock()
        sys.modules["anthropic"] = mock_anthropic_module

        from src.llm.anthropic_client import AnthropicClient

        client = AnthropicClient(api_key="test-key")
        assert client.model == "claude-sonnet-4-6"
        mock_anthropic_module.Anthropic.assert_called_once_with(api_key="test-key")

        del sys.modules["anthropic"]

    def test_create_client_custom_model(self):
        """测试使用自定义模型创建客户端"""
        mock_anthropic_module = MagicMock()
        sys.modules["anthropic"] = mock_anthropic_module

        from src.llm.anthropic_client import AnthropicClient

        client = AnthropicClient(api_key="test-key", model="claude-opus-4-6")
        assert client.model == "claude-opus-4-6"

        del sys.modules["anthropic"]

    def test_chat(self):
        """测试聊天功能"""
        mock_anthropic_module = MagicMock()
        sys.modules["anthropic"] = mock_anthropic_module

        from src.llm.anthropic_client import AnthropicClient

        # Mock 响应
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Test response"
        mock_response.content = [mock_content]
        mock_response.model = "claude-sonnet-4-6"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.model_dump.return_value = {}

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_module.Anthropic.return_value = mock_client

        client = AnthropicClient(api_key="test-key")
        response = client.chat("system", "user")

        assert response.content == "Test response"
        assert response.model == "claude-sonnet-4-6"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 5

        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["system"] == "system"
        assert call_args.kwargs["messages"][0]["content"] == "user"

        del sys.modules["anthropic"]

    def test_is_available_with_key(self):
        """测试有 API Key 时可用性检查"""
        mock_anthropic_module = MagicMock()
        sys.modules["anthropic"] = mock_anthropic_module

        from src.llm.anthropic_client import AnthropicClient

        client = AnthropicClient(api_key="test-key")
        assert client.is_available() is True

        del sys.modules["anthropic"]

    def test_is_available_without_key(self):
        """测试无 API Key 时可用性检查"""
        mock_anthropic_module = MagicMock()
        sys.modules["anthropic"] = mock_anthropic_module

        from src.llm.anthropic_client import AnthropicClient

        with patch.dict("os.environ", {}, clear=True):
            client = AnthropicClient(api_key=None)
            assert client.is_available() is False

        del sys.modules["anthropic"]


class TestOllamaClient:
    """Ollama 客户端测试"""

    def test_create_client_default_params(self):
        """测试使用默认参数创建客户端"""
        from src.llm.ollama_client import OllamaClient

        client = OllamaClient()
        assert client.model == "qwen2.5:7b"
        assert client.base_url == "http://localhost:11434"

    def test_create_client_custom_params(self):
        """测试使用自定义参数创建客户端"""
        from src.llm.ollama_client import OllamaClient

        client = OllamaClient(model="llama3", base_url="http://localhost:8080")
        assert client.model == "llama3"
        assert client.base_url == "http://localhost:8080"

    @patch("src.llm.ollama_client.requests.post")
    def test_chat(self, mock_post):
        """测试聊天功能"""
        from src.llm.ollama_client import OllamaClient

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Test response"},
            "model": "qwen2.5:7b",
            "prompt_eval_count": 10,
            "eval_count": 5
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        client = OllamaClient()
        response = client.chat("system", "user")

        assert response.content == "Test response"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 5

    @patch("src.llm.ollama_client.requests.post")
    def test_chat_with_custom_params(self, mock_post):
        """测试使用自定义参数聊天"""
        from src.llm.ollama_client import OllamaClient

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Response"},
            "model": "qwen2.5:7b",
            "prompt_eval_count": 5,
            "eval_count": 3
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        client = OllamaClient()
        response = client.chat("system", "user", max_tokens=1000, temperature=0.5)

        call_args = mock_post.call_args
        options = call_args.kwargs["json"]["options"]
        assert options["num_predict"] == 1000
        assert options["temperature"] == 0.5

    @patch("src.llm.ollama_client.requests.get")
    def test_is_available_success(self, mock_get):
        """测试服务可用时返回 True"""
        from src.llm.ollama_client import OllamaClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = OllamaClient()
        assert client.is_available() is True

    @patch("src.llm.ollama_client.requests.get")
    def test_is_available_failure(self, mock_get):
        """测试服务不可用时返回 False"""
        from src.llm.ollama_client import OllamaClient

        mock_get.side_effect = Exception("Connection error")

        client = OllamaClient()
        assert client.is_available() is False

    @patch("src.llm.ollama_client.requests.get")
    def test_is_available_wrong_status(self, mock_get):
        """测试服务返回非 200 状态码"""
        from src.llm.ollama_client import OllamaClient

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        client = OllamaClient()
        assert client.is_available() is False

    @patch("src.llm.ollama_client.requests.get")
    def test_list_models(self, mock_get):
        """测试列出可用模型"""
        from src.llm.ollama_client import OllamaClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:7b"},
                {"name": "llama3:8b"}
            ]
        }
        mock_get.return_value = mock_response

        client = OllamaClient()
        models = client.list_models()

        assert models == ["qwen2.5:7b", "llama3:8b"]

    @patch("src.llm.ollama_client.requests.get")
    def test_list_models_on_error(self, mock_get):
        """测试列出模型时出错"""
        from src.llm.ollama_client import OllamaClient

        mock_get.side_effect = Exception("Connection error")

        client = OllamaClient()
        models = client.list_models()

        assert models == []


class TestFactory:
    """工厂函数测试"""

    @patch("src.llm.factory.OpenAIClient")
    def test_create_openai_client_default_model(self, mock):
        from src.llm.factory import create_llm_client

        config = {"provider": "openai"}
        create_llm_client(config)
        mock.assert_called_once_with(
            model="gpt-4o-mini",
            api_key=None,
            base_url=None
        )

    @patch("src.llm.factory.OpenAIClient")
    def test_create_openai_client_custom_model(self, mock):
        from src.llm.factory import create_llm_client

        config = {"provider": "openai", "model": "gpt-4"}
        create_llm_client(config)
        mock.assert_called_once_with(
            model="gpt-4",
            api_key=None,
            base_url=None
        )

    @patch("src.llm.factory.OpenAIClient")
    def test_create_openai_client_with_all_params(self, mock):
        from src.llm.factory import create_llm_client

        config = {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "test-key",
            "base_url": "https://api.example.com"
        }
        create_llm_client(config)
        mock.assert_called_once()

    @patch("src.llm.factory.AnthropicClient")
    def test_create_anthropic_client(self, mock):
        from src.llm.factory import create_llm_client

        config = {"provider": "anthropic"}
        create_llm_client(config)
        mock.assert_called_once_with(
            model="claude-sonnet-4-6",
            api_key=None
        )

    @patch("src.llm.factory.AnthropicClient")
    def test_create_anthropic_client_custom_model(self, mock):
        from src.llm.factory import create_llm_client

        config = {"provider": "anthropic", "model": "claude-opus-4-6"}
        create_llm_client(config)
        mock.assert_called_once()

    @patch("src.llm.factory.OllamaClient")
    def test_create_ollama_client(self, mock):
        from src.llm.factory import create_llm_client

        config = {"provider": "ollama"}
        create_llm_client(config)
        mock.assert_called_once_with(
            model="qwen2.5:7b",
            base_url=None
        )

    @patch("src.llm.factory.OllamaClient")
    def test_create_ollama_client_custom_params(self, mock):
        from src.llm.factory import create_llm_client

        config = {
            "provider": "ollama",
            "model": "llama3",
            "base_url": "http://localhost:8080"
        }
        create_llm_client(config)
        mock.assert_called_once()

    def test_unsupported_provider(self):
        from src.llm.factory import create_llm_client

        with pytest.raises(ValueError, match="不支持的 LLM 提供方"):
            create_llm_client({"provider": "unknown"})

    @patch("src.llm.factory.OllamaClient")
    def test_default_provider_is_ollama(self, mock):
        from src.llm.factory import create_llm_client

        create_llm_client({})
        mock.assert_called_once()
