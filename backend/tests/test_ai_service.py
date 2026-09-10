import pytest
import httpx
from unittest.mock import patch, AsyncMock
from app.core.config import settings
from app.services.ai_service import OllamaAIService, BaseAIService, ai_service
from app.schemas.ai import AIStatusResponse, AITestPromptResponse


def test_ai_service_interface_and_configuration():
    """
    Requirement:
    - Model name must be configurable through environment variables.
    - Do not hard-code a model.
    - Abstraction layer so rest of app does not depend directly on Ollama.
    """
    service = OllamaAIService()
    assert isinstance(service, BaseAIService)
    assert service.default_model == settings.OLLAMA_MODEL
    assert service.base_url == settings.OLLAMA_BASE_URL.rstrip("/")
    assert service.timeout_seconds == settings.OLLAMA_TIMEOUT_SECONDS


@pytest.mark.anyio
async def test_ollama_health_success():
    service = OllamaAIService()

    mock_response = httpx.Response(
        status_code=200,
        json={
            "models": [
                {"name": "llama3.2:latest"},
                {"name": "llama2:latest"}
            ]
        },
        request=httpx.Request("GET", "http://localhost:11434/api/tags")
    )

    with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_response)):
        status = await service.check_health()
        assert status.isAvailable is True
        assert status.provider == "Ollama"
        assert "llama3.2:latest" in status.availableModels
        assert status.error is None



@pytest.mark.anyio
async def test_ollama_health_connection_refused_graceful_handling():
    """
    Requirement:
    - Handle Ollama unavailable errors gracefully.
    - Application must continue working if AI is unavailable.
    """
    service = OllamaAIService()

    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
        status = await service.check_health()
        assert status.isAvailable is False
        assert status.provider == "Ollama"
        assert status.error == "CONNECTION_REFUSED"
        assert "offline" in status.message.lower() or "not installed" in status.message.lower()


@pytest.mark.anyio
async def test_ollama_health_timeout_graceful_handling():
    """
    Requirement:
    - Add timeout handling.
    """
    service = OllamaAIService()

    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timed out")):
        status = await service.check_health()
        assert status.isAvailable is False
        assert status.error == "TIMEOUT"


@pytest.mark.anyio
async def test_ollama_generate_text_success():
    service = OllamaAIService()

    mock_response = httpx.Response(
        status_code=200,
        json={
            "model": "llama3.2",
            "response": "Under standard consumer warranty terms, panel defects are covered for 2 years.",
            "done": True
        },
        request=httpx.Request("POST", "http://localhost:11434/api/generate")
    )

    with patch("httpx.AsyncClient.post", AsyncMock(return_value=mock_response)):
        res = await service.generate_text(
            prompt="What does panel warranty cover?",
            system_prompt="You are a warranty expert.",
            temperature=0.5
        )
        assert res.success is True
        assert res.model == "llama3.2"
        assert "panel defects are covered" in res.response
        assert res.error is None
        assert res.durationMs is not None



@pytest.mark.anyio
async def test_ollama_generate_text_timeout_handling():
    """
    Requirement:
    - Timeout handling without crashing backend.
    """
    service = OllamaAIService()

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timed out")):
        res = await service.generate_text(
            prompt="Test prompt that takes too long"
        )
        assert res.success is False
        assert "timed out" in res.error.lower()
        assert res.response == ""
