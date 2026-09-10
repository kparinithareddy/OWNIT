from fastapi import APIRouter, Depends, status
from app.schemas.user import UserResponse
from app.schemas.ai import (
    AIStatusResponse,
    AITestPromptRequest,
    AITestPromptResponse
)
from app.api.dependencies import get_current_user
from app.services.ai_service import ai_service

router = APIRouter()


@router.get(
    "/status",
    response_model=AIStatusResponse,
    summary="Check local AI / Ollama status",
    description="Polls the local Ollama service to check availability, installed models, and server health. Always returns 200 OK with graceful status flags."
)
async def get_ai_status(
    current_user: UserResponse = Depends(get_current_user)
) -> AIStatusResponse:
    """
    Returns Ollama health status, configured model, and locally available model tags.
    Does NOT expose Ollama directly to the client browser.
    """
    return await ai_service.check_health()


@router.post(
    "/test",
    response_model=AITestPromptResponse,
    summary="Test local AI text generation",
    description="Sends a test prompt to the local Ollama LLM to verify prompt processing and response time."
)
async def test_ai_prompt(
    data: AITestPromptRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> AITestPromptResponse:
    """
    Executes a test generation prompt via the AI service abstraction.
    Handles errors and timeouts safely without crashing the backend.
    """
    return await ai_service.generate_text(
        prompt=data.prompt,
        system_prompt=data.systemPrompt,
        temperature=data.temperature or 0.7
    )
