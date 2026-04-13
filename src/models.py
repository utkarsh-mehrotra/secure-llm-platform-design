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

class SystemChannel(BaseModel):
    prompt: str
    policies: Dict[str, Any]
    signature: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expiry: datetime

    def is_valid(self, hmac_key: str) -> bool:
        import hmac, hashlib, json
        payload = f"{self.prompt}|{json.dumps(self.policies, sort_keys=True)}"
        expected_sig = hmac.new(
            hmac_key.encode(), 
            payload.encode(), 
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(self.signature, expected_sig)

class UserChannel(BaseModel):
    user_id: str
    query: str
    permissions: List[str]
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def scope_to_permissions(self, requested_tool: str) -> bool:
        return f"use_{requested_tool}" in self.permissions

class DataChannel(BaseModel):
    documents: List[str]
    sources: List[Dict[str, Any]]
    sanitization_audit: Dict[str, Any]

class MessageChannel(BaseModel):
    role: str # Keep for legacy compatibility during migration
    content: str
    trust: Optional[TrustManifest] = None

class MultiChannelInput(BaseModel):
    system_instructions: SystemChannel
    user_request: UserChannel
    retrieved_data: DataChannel

class AuditEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    user_id: str
    tool_name: Optional[str] = None
    action_status: str
    reason: Optional[str] = None
    sanitization_audit: Optional[Dict[str, Any]] = None
    token_id_hash: Optional[str] = None
    request_params_hash: Optional[str] = None
    source_ip: str
    session_id: str
    outcome: str

    def to_log_entry(self) -> str:
        import json
        return json.dumps(self.model_dump(mode='json'))

class Alert(BaseModel):
    severity: str
    message: str
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExecutionEvent(BaseModel):
    token: Optional[str] = None
    tool: str
    params: Dict[str, Any]
    user_id: str
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sanitization_audit: Dict[str, Any] = Field(default_factory=dict)

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

class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"

class LLMConfig(BaseModel):
    provider: ModelProvider
    model_name: str
    endpoint_url: Optional[str] = None
    api_key: Optional[str] = None # Masked in UI

class SecureUserQuery(BaseModel):
    query: str
    user_id: str
    session_id: Optional[str] = None
    llm_config: Optional[LLMConfig] = None

class ToolResponse(BaseModel):
    status: str
    result: Any
    manifest: Optional[TrustManifest] = None
