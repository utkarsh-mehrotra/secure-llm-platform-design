from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid

# Local imports
from .models import TrustManifest, CapabilityToken, ToolRequest, ToolResponse
from .policy import PolicyEngine
from .sanitizer import ContextSanitizer
from .gateway import ToolGateway, ToolRegistry
from .orchestrator import Orchestrator

app = FastAPI(title="Secure LLM Platform")

# --- Dependency Injection & State ---
# In production, use a secure secret from KMS
MASTER_KEY = "staff_level_super_secret_key_123456"

registry = ToolRegistry()
policy_engine = PolicyEngine(master_key=MASTER_KEY)
sanitizer = ContextSanitizer()
gateway = ToolGateway(registry, policy_engine)
orchestrator = Orchestrator(policy_engine=policy_engine, sanitizer=sanitizer, gateway=gateway)

# --- Mock Tool Definitions ---
def database_lookup(query: str) -> str:
    # A simple mock tool
    if "ceo_email" in query:
        return "ceo@company.com"
    return f"No results found for {query}"

registry.register("database_lookup", database_lookup)

# --- API Models ---
class SecureUserQuery(BaseModel):
    query: str
    user_id: str
    session_id: Optional[str] = None

# --- Routes ---
@app.post("/v1/query")
async def secure_query(req: SecureUserQuery):
    """
    Entry point for secure LLM interaction.
    Enforces the complete data plane isolation and capability flow.
    """
    session_id = req.session_id or str(uuid.uuid4())
    try:
        result = await orchestrator.process_request(
            user_query=req.query,
            user_id=req.user_id,
            session_id=session_id,
            llm_config=req.llm_config
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "secure-llm-platform"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
