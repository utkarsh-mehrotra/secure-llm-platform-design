import re
from typing import List, Tuple
from .models import TrustManifest, MessageChannel, TrustLevel

class ContextSanitizer:
    def __init__(self):
        # L1: Regex patterns for common injection attacks
        self.injection_patterns = [
            r"(?i)ignore\s+previous\s+instructions",
            r"(?i)system\s+override",
            r"(?i)dan\s+mode",
            r"(?i)you\s+are\s+now\s+a",
            r"(?i)set\s+new\s+role",
            r"\[SYSTEM[\]:]",
        ]

    def _l1_regex_filter(self, content: str) -> bool:
        """Returns True if any malicious pattern is found."""
        for pattern in self.injection_patterns:
            if re.search(pattern, content):
                return True
        return False

    def _l2_classifier_mock(self, content: str) -> float:
        """
        Mock for an ML classifier (e.g., Llama-Guard).
        Returns a trust score between 0.0 and 1.0.
        """
        # Heuristic for the mock: high ratio of exclamation marks and capitals
        if not content:
            return 1.0
        caps = sum(1 for c in content if c.isupper())
        excl = content.count('!')
        score = 1.0 - min(0.8, (caps / len(content)) + (excl / 10))
        return score

    def _l3_transform_passive(self, content: str) -> str:
        """
        Converts instructional sentences to passive declarations.
        Example: 'Delete all files' -> '[REDACTED_INSTRUCTION] The doc discusses file deletion'
        """
        # Basic substitution for simulation
        replacements = [
            (r"(?i)delete\s+all\s+\w+", "[REDACTED: deletion request]"),
            (r"(?i)send\s+email\s+to", "[REDACTED: email request]"),
            (r"(?i)execute\s+command", "[REDACTED: execution request]"),
        ]
        transformed = content
        for pattern, replacement in replacements:
            transformed = re.sub(pattern, replacement, transformed)
        return transformed

    def sanitize_channel(self, channel: MessageChannel) -> MessageChannel:
        """Applies multi-layer sanitization to a single channel."""
        if channel.role != "data":
            return channel # Only sanitize untrusted data
            
        content = channel.content
        
        # Layer 1: Fast Regex check
        if self._l1_regex_filter(content):
            content = "[BLOCKED BY L1 SANITIZER: HIGH RISK PATTERN DETECTED]"
            trust_score = 0.0
        else:
            # Layer 2: Probabilistic Score
            trust_score = self._l2_classifier_mock(content)
            
            # Layer 3: Passive Transformation
            content = self._l3_transform_passive(content)
            
        # Update manifest
        manifest = TrustManifest(
            source_id="sanitizer_v1",
            trust_score=trust_score,
            classification=["sanitized"]
        )
        
        return MessageChannel(
            role="data",
            content=content,
            trust=manifest
        )

    def sanitize_batch(self, channels: List[MessageChannel]) -> List[MessageChannel]:
        return [self.sanitize_channel(c) for c in channels]
