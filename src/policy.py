import hmac
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .models import CapabilityToken, ParameterConstraint
from .clop import CLOP, MetaLearner, ConstraintPolicy, Interaction

class MockVaultClient:
    """A mock Vault to support local key rotation testing."""
    def __init__(self, path: str = "vault_mock.json"):
        self.path = path
        if not os.path.exists(self.path):
            self._init_vault()

    def _init_vault(self):
        initial_data = {
            "current_key_id": f"key_{datetime.utcnow().strftime('%Y%m%d')}",
            "current_key": secrets.token_hex(32),
            "previous_key_id": None,
            "previous_key": None
        }
        self.write("secret/llm-security/hmac-keys", initial_data)

    def read(self, path: str) -> Dict[str, Any]:
        with open(self.path, 'r') as f:
            data = json.load(f)
        return data.get(path, {})

    def write(self, path: str, data: Dict[str, Any]):
        try:
            with open(self.path, 'r') as f:
                all_data = json.load(f)
        except Exception:
            all_data = {}
        all_data[path] = data
        with open(self.path, 'w') as f:
            json.dump(all_data, f)

class KeyRotationManager:
    """Manage HMAC key rotation."""
    def __init__(self, rotation_period_days: int = 7):
        self.vault = MockVaultClient()
        self.rotation_period = rotation_period_days
        self.keys = {}
        self.current_key_id = None
        self._load_keys_from_vault()
        
    def _load_keys_from_vault(self):
        keys_metadata = self.vault.read("secret/llm-security/hmac-keys")
        self.current_key_id = keys_metadata.get("current_key_id")
        self.keys[self.current_key_id] = keys_metadata.get("current_key")
        if keys_metadata.get("previous_key_id"):
            self.keys[keys_metadata["previous_key_id"]] = keys_metadata.get("previous_key")
            
    def _perform_rotation(self):
        new_key = secrets.token_hex(32)
        new_key_id = f"key_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        self.vault.write(
            "secret/llm-security/hmac-keys",
            {
                "current_key_id": new_key_id,
                "current_key": new_key,
                "previous_key_id": self.current_key_id,
                "previous_key": self.keys.get(self.current_key_id),
                "rotated_at": datetime.utcnow().isoformat(),
            }
        )
        self.keys[new_key_id] = new_key
        self.current_key_id = new_key_id

    def sign_token(self, payload: str) -> str:
        current_key = self.keys[self.current_key_id]
        return hmac.new(
            current_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def verify_token(self, payload: str, signature: str) -> bool:
        for key_id, key_material in self.keys.items():
            if not key_material:
                continue
            expected_sig = hmac.new(
                key_material.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            if hmac.compare_digest(signature, expected_sig):
                return True
        return False

class PolicyEngine:
    def __init__(self):
        self.key_manager = KeyRotationManager()
        
        # Initialize CLOP with dummy data
        dummy_interactions = [
            Interaction("user1", "database_lookup", {"query": "test"}, datetime.utcnow())
        ]
        self.clop = CLOP(dummy_interactions)
        learned = self.clop.learn()
        self.meta_learner = MetaLearner(learned)

    def mint_token(
        self, 
        tool_id: str, 
        session_id: str, 
        manual_constraints: Optional[Dict[str, ParameterConstraint]] = None,
        ttl_minutes: int = 15
    ) -> CapabilityToken:
        """Issues a new signed capability token utilizing CLOP rules."""
        
        # 1. Fetch generalized constraints from MetaLearner
        learned_policy = self.meta_learner.predict_constraints_for_new_tool(tool_id)
        learned_constraints = learned_policy.to_dict()
        
        final_constraints = {**manual_constraints, **learned_constraints} if manual_constraints else learned_constraints
        
        token_id = hashlib.sha256(f"{tool_id}-{session_id}-{datetime.utcnow().isoformat()}".encode('utf-8')).hexdigest()[:16]
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        
        token_data = {
            "token_id": token_id,
            "tool_id": tool_id,
            "session_id": session_id,
            "expires_at": expires_at.isoformat(),
            "constraints": {k: v.model_dump() for k, v in final_constraints.items()}
        }
        
        # 2. Sign using KeyRotationManager
        data_str = json.dumps(token_data, sort_keys=True)
        signature = self.key_manager.sign_token(data_str)
        
        return CapabilityToken(
            token_id=token_id,
            tool_id=tool_id,
            session_id=session_id,
            expires_at=expires_at,
            constraints=final_constraints,
            signature=signature
        )

    def verify_token(self, token: CapabilityToken) -> bool:
        """Verifies HMAC signature across valid keys."""
        if token.is_expired:
            return False
            
        token_data = {
            "token_id": token.token_id,
            "tool_id": token.tool_id,
            "session_id": token.session_id,
            "expires_at": token.expires_at.isoformat(),
            "constraints": {k: v.model_dump() for k, v in token.constraints.items()}
        }
        
        data_str = json.dumps(token_data, sort_keys=True)
        return self.key_manager.verify_token(data_str, token.signature)
