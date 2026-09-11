from fastapi import APIRouter, Depends, status
from typing import List, Optional
from app.schemas.user import UserResponse
from app.schemas.ai import (
    AIStatusResponse,
    AITestPromptRequest,
    AITestPromptResponse,
    AIConversationCreate,
    AIConversationResponse,
    AIConversationListResponse,
    AIMessageSendRequest,
    AIMessageResponse,
    AIConversationDetailResponse
)
from app.schemas.chat import (
    ChatSendRequest,
    ChatResponse,
    ChatHistoryResponse
)
from app.api.dependencies import get_current_user
from app.services.ai_service import ai_service
from app.services.chat_service import chat_service
from app.services.product_service import product_service
from app.services.ai.assistant_service import assistant_service
from app.services.ai.conversation_service import (
    conversation_service,
    format_conversation_doc,
    format_message_doc
)

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


# -------------------------------------------------------------
# Modular Global & Product AI Conversation Endpoints
# -------------------------------------------------------------

@router.post(
    "/conversations",
    response_model=AIConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new AI conversation thread",
    description="Creates a new multi-turn conversation thread in either Global or Product context mode."
)
async def create_conversation(
    data: AIConversationCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> AIConversationResponse:
    prod_name = None
    if data.contextType == "product" and data.productId:
        prod = await product_service.get_product_by_id(data.productId, current_user.id)
        prod_name = prod.name

    doc = await conversation_service.create_conversation(
        user_id=current_user.id,
        context_type=data.contextType,
        product_id=data.productId,
        product_name=prod_name,
        title=data.title
    )
    return format_conversation_doc(doc, message_count=0)


@router.get(
    "/conversations",
    response_model=AIConversationListResponse,
    summary="List user's AI conversations",
    description="Retrieves all active conversation threads for the authenticated user, sorted by last updated."
)
async def list_conversations(
    current_user: UserResponse = Depends(get_current_user)
) -> AIConversationListResponse:
    docs = await conversation_service.list_conversations(current_user.id)
    items = []
    for d in docs:
        c_id = str(d["_id"])
        msgs = await conversation_service.get_messages(c_id, current_user.id, limit=100)
        items.append(format_conversation_doc(d, message_count=len(msgs)))
    return AIConversationListResponse(conversations=items, total=len(items))


@router.get(
    "/conversations/{conversation_id}",
    response_model=AIConversationDetailResponse,
    summary="Get conversation details and messages",
    description="Loads a specific conversation thread and its message history for the owner."
)
async def get_conversation_detail(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> AIConversationDetailResponse:
    conv = await conversation_service.get_conversation(conversation_id, current_user.id)
    msgs = await conversation_service.get_messages(conversation_id, current_user.id, limit=100)
    formatted_msgs = [format_message_doc(m) for m in msgs]
    return AIConversationDetailResponse(
        conversation=format_conversation_doc(conv, message_count=len(formatted_msgs)),
        messages=formatted_msgs
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AIMessageResponse,
    summary="Send a message in an AI conversation thread",
    description="Processes user message with targeted retrieval, local Ollama inference, source transparency, and action generation."
)
async def send_conversation_message(
    conversation_id: str,
    data: AIMessageSendRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> AIMessageResponse:
    return await assistant_service.process_message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        request=data
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an AI conversation thread",
    description="Permanently deletes the conversation thread and its message logs."
)
async def delete_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    await conversation_service.delete_conversation(conversation_id, current_user.id)
    return {
        "success": True,
        "message": f"Conversation {conversation_id} deleted successfully."
    }


# -------------------------------------------------------------
# Backward-Compatible Legacy Product Chat Endpoints
# -------------------------------------------------------------

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


