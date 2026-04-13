from typing import List, Dict, Tuple, Any
from datetime import datetime
from collections import defaultdict
from .models import AuditEvent, Alert, ExecutionEvent

class AnomalyDetector:
    """Real-time detection of attack patterns."""
    
    def __init__(self, alert_threshold: float = 0.8):
        self.threshold = alert_threshold
        self.baseline_metrics = self._compute_baseline()
        
    def _compute_baseline(self) -> Dict[str, float]:
        # Return a stub baseline
        return {"rejection_rate": 0.05}
        
    def check_for_anomalies(self, recent_events: List[ExecutionEvent]) -> List[Alert]:
        """Analyze recent events for attack signals."""
        alerts = []
        if not recent_events:
            return alerts
            
        rejection_rate = self._compute_rejection_rate(recent_events)
        if rejection_rate > self.baseline_metrics["rejection_rate"] * 2:
            alerts.append(Alert(
                severity="HIGH",
                message=f"Token rejection rate spike: {rejection_rate:.2f}",
                action="Investigate tool gateway logs; consider rate limiting"
            ))
            
        reused_tokens = self._detect_token_reuse(recent_events)
        if len(reused_tokens) > 5:
            alerts.append(Alert(
                severity="CRITICAL",
                message=f"Possible replay attack: {len(reused_tokens)} tokens reused",
                action="Revoke all reused tokens; investigate source"
            ))
            
        unusual_tools = self._detect_unusual_invocations(recent_events)
        if len(unusual_tools) > 3:
            alerts.append(Alert(
                severity="MEDIUM",
                message=f"Unusual tool invocations: {unusual_tools}",
                action="Review and approve unusual tool uses"
            ))
            
        high_l2_events = [e for e in recent_events if e.sanitization_audit.get("l2_score", 0.0) > 0.85]
        if len(high_l2_events) > 10:
            alerts.append(Alert(
                severity="MEDIUM",
                message=f"High L2 threat scores in data channel ({len(high_l2_events)} events)",
                action="Review data sources; consider quarantining high-risk sources"
            ))
            
        return alerts
        
    def _compute_rejection_rate(self, events: List[ExecutionEvent]) -> float:
        fails = sum(1 for e in events if e.status == "error")
        return fails / len(events) if events else 0.0
        
    def _detect_token_reuse(self, events: List[ExecutionEvent]) -> List[str]:
        token_counts = defaultdict(int)
        for event in events:
            if event.token:
                token_counts[event.token] += 1
        return [token for token, count in token_counts.items() if count > 1]
        
    def _detect_unusual_invocations(self, events: List[ExecutionEvent]) -> List[str]:
        # Dummy stub for unusually high tool invocation count
        return []

class DecisionAttestation:
    """High-impact decision attestation."""
    def __init__(self, decision: str, reasoning: str, data_citations: List[str]):
        self.decision = decision
        self.reasoning = reasoning
        self.data_citations = data_citations
        self.timestamp = datetime.utcnow()
        
    def verify(self, sanitized_data_audit: Dict[str, Any]) -> Tuple[bool, str]:
        suspicious_phrases = ["[REDACTED", "unusual", "override", "bypass"]
        for phrase in suspicious_phrases:
            if phrase in self.reasoning:
                return False, f"Decision reasoning contains marker: {phrase}"
                
        # Heuristic L2 score flag
        if sanitized_data_audit.get("l2_score", 0.0) > 0.7:
            return True, "Approved, but flagged for human review (high L2 score)"
            
        return True, "Attestation verified"
