import logging
import time
from typing import List, Optional
import httpx
from app.core.config import settings
from app.schemas.ai import AIStatusResponse, AITestPromptResponse

logger = logging.getLogger("ownit.services.ai.ollama")


class OllamaService:
    """
    Client for interacting with local Ollama inference server.
    Features graceful timeout management, connection fallback, and zero-crash error handling.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = float(getattr(settings, "OLLAMA_TIMEOUT", 25.0))

    async def check_health(self) -> AIStatusResponse:
        """
        Polls Ollama `/api/tags` endpoint to verify connectivity and list installed models.
        """
        endpoint = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                response = await client.get(endpoint)
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return AIStatusResponse(
                        isAvailable=True,
                        provider="Ollama",
                        configuredModel=self.model,
                        availableModels=models,
                        baseUrl=self.base_url,
                        message="Local Ollama instance is online and operational."
                    )
                else:
                    return AIStatusResponse(
                        isAvailable=False,
                        provider="Ollama",
                        configuredModel=self.model,
                        availableModels=[],
                        baseUrl=self.base_url,
                        message=f"Ollama returned HTTP status {response.status_code}",
                        error=response.text
                    )
        except httpx.ConnectError:
            return AIStatusResponse(
                isAvailable=False,
                provider="Ollama",
                configuredModel=self.model,
                availableModels=[],
                baseUrl=self.base_url,
                message="Cannot connect to Ollama. Ensure Ollama is running locally (e.g. `ollama serve`).",
                error="Connection refused"
            )
        except httpx.TimeoutException:
            return AIStatusResponse(
                isAvailable=False,
                provider="Ollama",
                configuredModel=self.model,
                availableModels=[],
                baseUrl=self.base_url,
                message="Ollama health check timed out.",
                error="Timeout"
            )
        except Exception as e:
            return AIStatusResponse(
                isAvailable=False,
                provider="Ollama",
                configuredModel=self.model,
                availableModels=[],
                baseUrl=self.base_url,
                message="Unexpected error connecting to Ollama.",
                error=str(e)
            )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        timeout_seconds: Optional[float] = None
    ) -> AITestPromptResponse:
        """
        Executes text generation via Ollama `/api/generate` endpoint.
        """
        endpoint = f"{self.base_url}/api/generate"
        start_time = time.time()
        timeout = timeout_seconds or self.timeout

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(endpoint, json=payload)
                duration_ms = round((time.time() - start_time) * 1000, 2)

                if response.status_code == 200:
                    data = response.json()
                    generated_text = data.get("response", "").strip()
                    return AITestPromptResponse(
                        success=True,
                        provider="Ollama",
                        model=self.model,
                        response=generated_text,
                        durationMs=duration_ms
                    )
                else:
                    return AITestPromptResponse(
                        success=False,
                        provider="Ollama",
                        model=self.model,
                        response="",
                        durationMs=duration_ms,
                        error=f"Ollama error {response.status_code}: {response.text}"
                    )
        except httpx.ConnectError:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return AITestPromptResponse(
                success=False,
                provider="Ollama",
                model=self.model,
                response="",
                durationMs=duration_ms,
                error="Cannot connect to Ollama at " + self.base_url
            )
        except httpx.TimeoutException:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return AITestPromptResponse(
                success=False,
                provider="Ollama",
                model=self.model,
                response="",
                durationMs=duration_ms,
                error=f"Ollama inference timed out after {timeout} seconds"
            )
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return AITestPromptResponse(
                success=False,
                provider="Ollama",
                model=self.model,
                response="",
                durationMs=duration_ms,
                error=str(e)
            )


ollama_service = OllamaService()
