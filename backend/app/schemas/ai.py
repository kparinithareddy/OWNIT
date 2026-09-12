from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from app.schemas.sources import SourceReference


class AIStatusResponse(BaseModel):
    isAvailable: bool = Field(..., description="Whether local Ollama instance is currently reachable")
    provider: str = Field(default="Ollama", description="Local AI engine provider name")
    configuredModel: str = Field(..., description="Model configured in environment variables (e.g. llama3.2)")
    availableModels: List[str] = Field(default_factory=list, description="List of models installed locally in Ollama")
    baseUrl: str = Field(..., description="Ollama backend connection URL")
    message: str = Field(..., description="Friendly status message")
    error: Optional[str] = Field(default=None, description="Connection error details if unavailable")


class AITestPromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="Test prompt to send to local model")
    systemPrompt: Optional[str] = Field(
        default="You are OWNIT Assistant, an expert on electronics, warranties, and maintenance. Keep answers concise and helpful.",
        description="Optional system prompt"
    )
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Sampling temperature")


class AITestPromptResponse(BaseModel):
    success: bool = Field(..., description="Whether inference completed successfully")
    provider: str = Field(default="Ollama", description="Local AI provider")
    model: str = Field(..., description="Name of model used for inference")
    response: str = Field(..., description="Generated text response from local LLM")
    durationMs: Optional[float] = Field(default=None, description="Execution duration in milliseconds")
    error: Optional[str] = Field(default=None, description="Error message if inference failed")


class AIAction(BaseModel):
    actionType: str = Field(..., description="Action type: view_product, view_warranty, view_document, prepare_claim, navigate")
    label: str = Field(..., description="User-facing button label")
    route: Optional[str] = Field(None, description="Frontend navigation route")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action payload parameters")


class AIConversationCreate(BaseModel):
    contextType: Literal["global", "product"] = Field(default="global", description="Conversation scope: global or product")
    productId: Optional[str] = Field(default=None, description="Product ID if contextType is product")
    title: Optional[str] = Field(default=None, description="Optional custom conversation title")


class AIConversationResponse(BaseModel):
    id: str = Field(..., description="Conversation ID")
    userId: str = Field(..., description="Owner user ID")
    contextType: Literal["global", "product"] = Field(default="global")
    productId: Optional[str] = None
    productName: Optional[str] = None
    title: str = Field(..., description="Conversation title")
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")
    lastMessage: Optional[str] = None
    messageCount: int = Field(default=0)


class AIConversationListResponse(BaseModel):
    conversations: List[AIConversationResponse] = Field(default_factory=list)
    total: int = Field(default=0)


class AIMessageSendRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User question or prompt")
    contextType: Optional[Literal["global", "product"]] = Field(default=None, description="Override context type if changing scope")
    productId: Optional[str] = Field(default=None, description="Target product ID if changing scope or overriding")


class AIMessageResponse(BaseModel):
    id: str = Field(..., description="Message ID")
    conversationId: str = Field(..., description="Associated conversation ID")
    role: Literal["user", "assistant", "system"] = Field(..., description="Message author role")
    content: str = Field(..., description="Message text content")
    sources: List[str] = Field(default_factory=list, description="Legacy string source labels")
    sourceReferences: List[SourceReference] = Field(default_factory=list, description="Structured verified source references")
    actions: List[AIAction] = Field(default_factory=list, description="Actionable buttons or links")
    createdAt: datetime = Field(..., description="Message timestamp")
    model: Optional[str] = Field(default=None, description="Model used for generation")
    durationMs: Optional[float] = Field(default=None, description="Inference execution duration")


class AIConversationDetailResponse(BaseModel):
    conversation: AIConversationResponse
    messages: List[AIMessageResponse] = Field(default_factory=list)


class SpeechToTextResponse(BaseModel):
    success: bool = Field(..., description="Whether audio transcription succeeded")
    transcript: str = Field(default="", description="Recognized speech text")
    language: str = Field(default="en-IN", description="Language code used for recognition")
    durationSeconds: Optional[float] = Field(default=None, description="Audio duration")
    error: Optional[str] = Field(default=None, description="Error message if transcription failed")


