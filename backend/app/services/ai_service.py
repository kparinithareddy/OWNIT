import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings
from app.schemas.ai import AIStatusResponse, AITestPromptResponse

logger = logging.getLogger("ownit.services.ai")


class BaseAIService(ABC):
    """
    Abstract AI Service interface ensuring the rest of the application
    does not depend directly on Ollama or any specific local AI vendor implementation.
    """

    @abstractmethod
    async def check_health(self) -> AIStatusResponse:
        """Checks if the local AI engine is online and returns installed models."""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """Returns the list of locally pulled/installed model tags."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> AITestPromptResponse:
        """Generates a text completion given a prompt."""
        pass


class OllamaAIService(BaseAIService):
    """
    Local AI Service implementation communicating with an Ollama instance.
    Runs completely on-premise/localhost with zero external API calls or costs.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model = settings.OLLAMA_MODEL
        self.timeout_seconds = settings.OLLAMA_TIMEOUT_SECONDS

    async def check_health(self) -> AIStatusResponse:
        """
        Polls Ollama `/api/tags` to verify connectivity and installed models.
        Handles connection errors and timeouts gracefully without raising exceptions.
        """
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    
                    is_configured_model_available = any(
                        self.default_model in m for m in models
                    )

                    msg = (
                        f"Ollama is running locally. Configured model '{self.default_model}' is ready."
                        if is_configured_model_available
                        else f"Ollama is online, but configured model '{self.default_model}' was not found in local library. Available: {', '.join(models) if models else 'None'}."
                    )

                    return AIStatusResponse(
                        isAvailable=True,
                        provider="Ollama",
                        configuredModel=self.default_model,
                        availableModels=models,
                        baseUrl=self.base_url,
                        message=msg,
                        error=None
                    )
                else:
                    return AIStatusResponse(
                        isAvailable=False,
                        provider="Ollama",
                        configuredModel=self.default_model,
                        availableModels=[],
                        baseUrl=self.base_url,
                        message=f"Ollama server responded with unexpected status code {res.status_code}.",
                        error=f"HTTP_{res.status_code}"
                    )
        except httpx.ConnectError:
            logger.warning("Local Ollama service is unreachable at %s", self.base_url)
            return AIStatusResponse(
                isAvailable=False,
                provider="Ollama",
                configuredModel=self.default_model,
                availableModels=[],
                baseUrl=self.base_url,
                message="Local Ollama service is offline or not installed. The application will continue operating with rule-based features.",
                error="CONNECTION_REFUSED"
            )
        except httpx.TimeoutException:
            logger.warning("Ollama connection timed out at %s", self.base_url)
            return AIStatusResponse(
                isAvailable=False,
                provider="Ollama",
                configuredModel=self.default_model,
                availableModels=[],
                baseUrl=self.base_url,
                message="Local Ollama service connection timed out.",
                error="TIMEOUT"
            )
        except Exception as exc:
            logger.error("Error connecting to Ollama: %s", exc)
            return AIStatusResponse(
                isAvailable=False,
                provider="Ollama",
                configuredModel=self.default_model,
                availableModels=[],
                baseUrl=self.base_url,
                message=f"Could not connect to Ollama: {str(exc)}",
                error=type(exc).__name__
            )

    async def list_models(self) -> List[str]:
        """Returns list of installed model names, or empty list if offline."""
        status = await self.check_health()
        return status.availableModels

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> AITestPromptResponse:
        """
        Sends generation request to Ollama `/api/generate`.
        Enforces timeout and returns structured response with execution duration.
        """
        target_model = model or self.default_model
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": temperature,
                "num_predict": 400
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(url, json=payload)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                if res.status_code == 200:
                    data = res.json()
                    response_text = data.get("response", "").strip()
                    return AITestPromptResponse(
                        success=True,
                        provider="Ollama",
                        model=target_model,
                        response=response_text,
                        durationMs=duration_ms,
                        error=None
                    )
                else:
                    err_msg = f"Ollama returned HTTP {res.status_code}: {res.text}"
                    logger.error(err_msg)
                    return AITestPromptResponse(
                        success=False,
                        provider="Ollama",
                        model=target_model,
                        response="",
                        durationMs=duration_ms,
                        error=err_msg
                    )
        except httpx.ConnectError:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning("Failed to connect to local Ollama service at %s", self.base_url)
            return AITestPromptResponse(
                success=False,
                provider="Ollama",
                model=target_model,
                response="",
                durationMs=duration_ms,
                error=f"Local Ollama server is offline at {self.base_url}. Please run 'ollama serve' or start the Ollama desktop app."
            )
        except httpx.TimeoutException:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.warning("Local Ollama generation timed out after %s seconds", self.timeout_seconds)
            return AITestPromptResponse(
                success=False,
                provider="Ollama",
                model=target_model,
                response="",
                durationMs=duration_ms,
                error=f"Local AI inference timed out after {self.timeout_seconds} seconds. The model may be busy loading into memory."
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error("Unexpected error in Ollama generation: %s", exc)
            return AITestPromptResponse(
                success=False,
                provider="Ollama",
                model=target_model,
                response="",
                durationMs=duration_ms,
                error=str(exc)
            )


# Default global AI Service instance
ai_service: BaseAIService = OllamaAIService()
