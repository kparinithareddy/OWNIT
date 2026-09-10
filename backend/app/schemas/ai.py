from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


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
