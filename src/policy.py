import hmac
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .models import CapabilityToken, ParameterConstraint

class PolicyEngine:
    def __init__(self, master_key: str):
        self.master_key = master_key.encode('utf-8')

    def _generate_signature(self, token_data: Dict[str, Any]) -> str:
        """Generates an HMAC-SHA256 signature for the token data."""
        # Ensure deterministic JSON string for signing
        data_str = json.dumps(token_data, sort_keys=True)
        return hmac.new(self.master_key, data_str.encode('utf-8'), hashlib.sha256).hexdigest()

    def mint_token(
        self, 
        tool_id: str, 
        session_id: str, 
        constraints: Dict[str, ParameterConstraint],
        ttl_minutes: int = 15
    ) -> CapabilityToken:
        """Issues a new short-lived, signed capability token."""
        token_id = hashlib.sha256(f"{tool_id}-{session_id}-{datetime.utcnow().isoformat()}".encode('utf-8')).hexdigest()[:16]
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        
        # Prepare data for signature (only immutable fields)
        token_data = {
            "token_id": token_id,
            "tool_id": tool_id,
            "session_id": session_id,
            "expires_at": expires_at.isoformat(),
            "constraints": {k: v.model_dump() for k, v in constraints.items()}
        }
        
        signature = self._generate_signature(token_data)
        
        return CapabilityToken(
            token_id=token_id,
            tool_id=tool_id,
            session_id=session_id,
            expires_at=expires_at,
            constraints=constraints,
            signature=signature
        )

    def verify_token(self, token: CapabilityToken) -> bool:
        """Verifies the HMAC signature and expiration status of a token."""
        if token.is_expired:
            return False
            
        # Reconstruct token data for verification
        token_data = {
            "token_id": token.token_id,
            "tool_id": token.tool_id,
            "session_id": token.session_id,
            "expires_at": token.expires_at.isoformat(),
            "constraints": {k: v.model_dump() for k, v in token.constraints.items()}
        }
        
        expected_signature = self._generate_signature(token_data)
        return hmac.compare_digest(expected_signature, token.signature)
