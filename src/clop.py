import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
from sklearn.ensemble import RandomForestClassifier

from .models import ParameterConstraint

class Constraint:
    """Base class for inferred constraints."""
    def check(self, value: Any) -> bool:
        raise NotImplementedError

class NumericConstraint(Constraint):
    def __init__(self, min_val: float, max_val: float):
        self.min_val = min_val
        self.max_val = max_val

    def check(self, value: Any) -> bool:
        try:
            v = float(value)
            return self.min_val <= v <= self.max_val
        except (ValueError, TypeError):
            return False
            
    def to_parameter_constraint(self) -> ParameterConstraint:
        # Regex could be built or just use max_value / numeric constructs
        # For simplicity in this platform, we rely on max_value
        return ParameterConstraint(max_value=self.max_val)

class CategoricalConstraint(Constraint):
    def __init__(self, allowed_values: set):
        self.allowed_values = allowed_values

    def check(self, value: Any) -> bool:
        return value in self.allowed_values
        
    def to_parameter_constraint(self) -> ParameterConstraint:
        return ParameterConstraint(allowed_values=list(self.allowed_values))

class TemporalConstraint:
    def __init__(self, max_per_day: int):
        self.max_per_day = max_per_day

class ConstraintPolicy:
    """Learned policy for a tool."""
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.constraints: Dict[str, Constraint] = {}
        self.temporal_constraint: Optional[TemporalConstraint] = None

    def add_constraint(self, param_name: str, constraint: Constraint):
        self.constraints[param_name] = constraint

    def accepts_params(self, params: Dict[str, Any]) -> bool:
        """Check if parameters satisfy all constraints."""
        for param_name, param_value in params.items():
            if param_name not in self.constraints:
                return False
            if not self.constraints[param_name].check(param_value):
                return False
        return True
        
    def to_dict(self) -> Dict[str, ParameterConstraint]:
        """Convert to the Pydantic-friendly dict."""
        out = {}
        for k, v in self.constraints.items():
            out[k] = v.to_parameter_constraint()
        return out
        
    def instantiate_for_tool(self, tool_name: str) -> "ConstraintPolicy":
        """Creates a clone with a different tool name."""
        cp = ConstraintPolicy(tool_name)
        cp.constraints = self.constraints.copy()
        cp.temporal_constraint = self.temporal_constraint
        return cp

class Interaction:
    def __init__(self, user: str, tool: str, params: Dict[str, Any], timestamp: datetime):
        self.user = user
        self.tool = tool
        self.params = params
        self.timestamp = timestamp

class CLOP:
    """Constraint Learning Over Periods."""
    
    def __init__(self, interaction_history: List[Interaction]):
        self.interactions = interaction_history
        self.learned_policies: Dict[str, ConstraintPolicy] = {}
    
    def learn(self) -> Dict[str, ConstraintPolicy]:
        """Learn constraints for all tools in interaction history."""
        tools = list(set(i.tool for i in self.interactions))
        
        for tool_name in tools:
            interactions = [i for i in self.interactions if i.tool == tool_name]
            policy = self._learn_policy_for_tool(tool_name, interactions)
            self.learned_policies[tool_name] = policy
        
        return self.learned_policies
    
    def _learn_policy_for_tool(self, tool_name: str, interactions: List[Interaction]) -> ConstraintPolicy:
        policy = ConstraintPolicy(tool_name)
        params_by_name = defaultdict(list)
        
        for interaction in interactions:
            for param_name, param_value in interaction.params.items():
                params_by_name[param_name].append(param_value)
        
        for param_name, values in params_by_name.items():
            constraint = self._infer_constraint(values)
            policy.add_constraint(param_name, constraint)
            
        timestamps = [i.timestamp for i in interactions]
        policy.temporal_constraint = self._infer_temporal_constraint(timestamps)
        
        return policy
    
    def _infer_constraint(self, values: List[Any]) -> Constraint:
        # Detect type
        if all(isinstance(v, (int, float)) for v in values if v is not None):
            numeric_values = [v for v in values if v is not None]
            if not numeric_values:
                return CategoricalConstraint(set())
            min_val, max_val = min(numeric_values), max(numeric_values)
            margin = 0.1 * (max_val - min_val) if max_val != min_val else min_val * 0.1
            return NumericConstraint(min_val - margin, max_val + margin)
        else:
            unique_vals = set(values)
            return CategoricalConstraint(unique_vals)
    
    def _infer_temporal_constraint(self, timestamps: List[datetime]) -> TemporalConstraint:
        if len(timestamps) < 2:
            return TemporalConstraint(max_per_day=100)
            
        sorted_ts = sorted(timestamps)
        deltas = [(sorted_ts[i+1] - sorted_ts[i]).total_seconds() for i in range(len(sorted_ts) - 1)]
        
        if not deltas:
            return TemporalConstraint(max_per_day=100)
            
        avg_delta = sum(deltas) / len(deltas)
        if avg_delta == 0:
            avg_delta = 1 # Avoid division by zero
            
        seconds_per_day = 86400
        max_per_day = int((seconds_per_day / avg_delta) * 1.5)
        return TemporalConstraint(max_per_day=max(max_per_day, 10))

class MetaLearner:
    """Generalize learned constraints to unseen tools."""
    
    def __init__(self, learned_policies: Dict[str, ConstraintPolicy]):
        self.policies = learned_policies
        self.tool_classifier = self._train_tool_classifier()
        
    def _extract_features(self, tool_name: str) -> List[float]:
        """Extremely simplified feature extractor for demonstration."""
        # E.g., length of name, contains 'transfer', etc.
        features = [
            len(tool_name),
            1 if 'transfer' in tool_name or 'pay' in tool_name else 0,
            1 if 'lookup' in tool_name or 'read' in tool_name else 0
        ]
        return features

    def _train_tool_classifier(self) -> RandomForestClassifier:
        X = []
        Y = []
        
        # We dummy-categorize tools for the Random Forest
        for tool_name, policy in self.policies.items():
            X.append(self._extract_features(tool_name))
            if "transfer" in tool_name:
                Y.append(1) # Financial Category
            else:
                Y.append(0) # Standard Category
                
        clf = RandomForestClassifier(n_estimators=10, max_depth=5, random_state=42)
        if X:
            clf.fit(X, Y)
        return clf
    
    def predict_constraints_for_new_tool(self, tool_name: str) -> ConstraintPolicy:
        """Predict constraints for a tool we've never seen before."""
        if not self.policies:
            return ConstraintPolicy(tool_name)
            
        features = self._extract_features(tool_name)
        
        # Ensure model is fitted
        try:
            tool_category = self.tool_classifier.predict([features])[0]
        except Exception:
            tool_category = 0
            
        # Find a template
        template_policy = None
        for name, pol in self.policies.items():
            has_financial = 1 if 'transfer' in name else 0
            if has_financial == tool_category:
                template_policy = pol
                break
                
        if not template_policy:
            template_policy = list(self.policies.values())[0]
            
        return template_policy.instantiate_for_tool(tool_name)
