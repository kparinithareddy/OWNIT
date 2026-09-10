from fastapi import APIRouter, Depends, status
from app.schemas.user import UserResponse
from app.schemas.ai import (
    AIStatusResponse,
    AITestPromptRequest,
    AITestPromptResponse
)
from app.schemas.chat import (
    ChatSendRequest,
    ChatResponse,
    ChatHistoryResponse
)
from app.api.dependencies import get_current_user
from app.services.ai_service import ai_service
from app.services.chat_service import chat_service

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


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send message to product AI assistant",
    description="Processes a multi-turn conversation turn anchored to a specific product's warranties, documents, maintenance history, and lifecycle status."
)
async def send_product_chat_message(
    data: ChatSendRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> ChatResponse:
    """
    Sends message with rich product context to Ollama and persists conversation in MongoDB.
    """
    return await chat_service.send_message(current_user.id, data)


@router.get(
    "/chat/{product_id}",
    response_model=ChatHistoryResponse,
    summary="Get product chat history",
    description="Fetches persistent conversation history between the owner and the AI assistant for a specific product."
)
async def get_product_chat_history(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> ChatHistoryResponse:
    """
    Retrieves chronological conversation history for the specified product.
    """
    return await chat_service.get_chat_history(product_id, current_user.id)


@router.delete(
    "/chat/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Clear product chat history",
    description="Deletes all conversation messages for a specific product."
)
async def clear_product_chat_history(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Clears chat history for the specified product.
    """
    await chat_service.clear_chat_history(product_id, current_user.id)
    return {
        "success": True,
        "message": f"Chat history cleared for product {product_id}."
    }

