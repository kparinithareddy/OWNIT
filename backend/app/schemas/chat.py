from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from app.schemas.sources import SourceReference


ChatMessageRole = Literal["user", "assistant", "system"]


class ChatMessage(BaseModel):
    id: str = Field(..., description="Unique message ID")
    role: ChatMessageRole = Field(..., description="Message author role: user or assistant")
    content: str = Field(..., description="Message text content")
    sources: List[str] = Field(default_factory=list, description="Legacy string source names")
    sourceReferences: List[SourceReference] = Field(default_factory=list, description="Structured 4-tier verified source references")
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")



class ChatSendRequest(BaseModel):
    productId: str = Field(..., min_length=1, description="Associated product ID")
    message: str = Field(..., min_length=1, max_length=3000, description="User question or instruction")


class ChatResponse(BaseModel):
    productId: str
    productName: str
    userMessage: ChatMessage
    assistantMessage: ChatMessage
    model: str = Field(..., description="Model used for generation")
    durationMs: Optional[float] = Field(default=None, description="Inference execution duration")


class ChatHistoryResponse(BaseModel):
    productId: str
    productName: str
    messages: List[ChatMessage] = Field(default_factory=list)
    totalMessages: int = 0
