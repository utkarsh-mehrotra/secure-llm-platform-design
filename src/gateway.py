import re
from typing import Dict, Any, Callable, Optional, List, Tuple
from .models import ToolRequest, ToolResponse, CapabilityToken
from .policy import PolicyEngine

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self.tools[name] = func

    def run(self, name: str, params: Dict[str, Any]) -> ToolResponse:
        if name not in self.tools:
            return ToolResponse(status="error", data=None, error=f"Tool '{name}' not found.")
        
        try:
            result = self.tools[name](**params)
            return ToolResponse(status="success", data=result)
        except Exception as e:
            return ToolResponse(status="error", data=None, error=str(e))

class ToolGateway:
    def __init__(self, registry: ToolRegistry, policy_engine: PolicyEngine):
        self.registry = registry
        self.policy_engine = policy_engine

    def _validate_constraints(self, token: CapabilityToken, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Checks if tool parameters meet the constraints defined in the token."""
        for param_name, constraint in token.constraints.items():
            if param_name not in params:
                continue # Optional parameter
            
            val = params[param_name]
            
            # 1. Regex Constraint
            if constraint.regex and not re.match(constraint.regex, str(val)):
                return False, f"Parameter '{param_name}' does not match regex constraint."
            
            # 2. Allowed Values Constraint
            if constraint.allowed_values and val not in constraint.allowed_values:
                return False, f"Parameter '{param_name}' is not in allowed list."
            
            # 3. Numeric Max Constraint
            if constraint.max_value is not None:
                try:
                    if float(val) > float(constraint.max_value):
                        return False, f"Parameter '{param_name}' exceeds maximum value."
                except (ValueError, TypeError):
                    return False, f"Parameter '{param_name}' is not a valid number."
                    
        return True, None

    def execute_with_token(self, tool_request: ToolRequest, token: CapabilityToken) -> ToolResponse:
        """Verified execution after checking token signature and constraints."""
        # 1. Verify Token Signature
        if not self.policy_engine.verify_token(token):
            return ToolResponse(status="error", data=None, error="Invalid or expired capability token signature.")
        
        # 2. Match Tool ID
        if token.tool_id != tool_request.tool_name:
            return ToolResponse(status="error", data=None, error="Token does not grant access to this tool.")

        # 3. Validate Parameter Constraints
        is_valid, error_msg = self._validate_constraints(token, tool_request.params)
        if not is_valid:
            return ToolResponse(status="error", data=None, error=f"Constraint violation: {error_msg}")

        # 4. Final Delegation
        return self.registry.run(tool_request.tool_name, tool_request.params)
