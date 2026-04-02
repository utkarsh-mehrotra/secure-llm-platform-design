from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

class TrustLevel(Enum):
    TRUSTED = "trusted"      # System provided
    UNTRUSTED = "untrusted"  # External/RAG data
    USER = "user"           # User input

class TrustManifest(BaseModel):
    source_id: str
    trust_score: float = Field(ge=0.0, le=1.0)
    classification: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signature: Optional[str] = None

class ParameterConstraint(BaseModel):
    regex: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    max_value: Optional[float] = None

class CapabilityToken(BaseModel):
    token_id: str
    tool_id: str
    session_id: str
    expires_at: datetime
    constraints: Dict[str, ParameterConstraint] = Field(default_factory=dict)
    signature: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

class MessageChannel(BaseModel):
    role: str # "system", "user", "data"
    content: str
    trust: Optional[TrustManifest] = None

class MultiChannelInput(BaseModel):
    system_instructions: MessageChannel
    user_request: MessageChannel
    retrieved_data: List[MessageChannel] = Field(default_factory=list)

class IntentType(Enum):
    SEARCH = "search"
    EXECUTE_TOOL = "execute_tool"
    FINAL_RESPONSE = "final_response"
    CLARIFICATION = "clarification"

class LLMIntentOutput(BaseModel):
    intent: IntentType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    capability_token: Optional[str] = None # The token required for this intent
    thought_process: Optional[str] = None

class ToolRequest(BaseModel):
    capability_token: str
    tool_name: str
    params: Dict[str, Any] = Field(default_factory=dict)

class ToolResponse(BaseModel):
    status: str
    data: Any
    error: Optional[str] = None
