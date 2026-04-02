# Implementation Plan: Security-Hardened LLM Platform (Staff Upgrade)

This plan outlines the transition from a "good" design to a **production-grade, security-hardened architecture** that provides hard guarantees against prompt injection and privilege escalation.

## User Review Required

> [!CAUTION]
> WE ARE MOVING FROM HEURISTICS TO DETERMINISM.
> The core shift is from "sanitizing strings" to "tokenizing capabilities". If the LLM does not have a valid, cryptographically verifiable Capability Token for an action, the ToolGateway will reject it regardless of the LLM's "intent".

> [!IMPORTANT]
> **Multi-Channel Isolation**: We will assume the underlying LLM API supports distinct channels (e.g., `developer`, `user`, `context`) that are technically isolated at the model level (e.g., via specific token prefixes or separate attention masks if available, or strict prompt engineering if using standard APIs).

## Proposed Hardened Components

### 1. The Isolation Layer (Data Plane)
- **Multi-Channel Input Builder**: Instead of a single string, this component builds a structured payload where `System`, `User`, and `UntrustedData` are strictly demarcated.
- **Multi-Layer Sanitizer**:
    - **L1 (Regex)**: Fast rejection of known exploit patterns.
    - **L2 (LLM Classifier)**: A small, specialized model (e.g., Llama-Guard) to score the risk of RAG content.
    - **L3 (Transformation)**: Converting instructional verbs in RAG into passive descriptions (e.g., "Delete all files" -> "[Instructional content removed: deletion request]").

### 2. The Privilege Layer (Control Plane)
- **Capability Token Mint**: Part of the `PolicyEngine`. Issues short-lived, HMAC-signed (or JWT-like) tokens that encapsulate:
    - `tool_id`
    - `param_constraints` (e.g., regex for paths, max value for amounts)
    - `session_id`
- **Hardened ToolGateway**: Validates the token and enforces constraints *outside* the LLM's influence.

### 3. Trust Execution Model
- **Trust-Aware Retriever**: Enforces per-tenant index isolation (physical or logical namespace separation).
- **Metadata Propagation**: Every object carries a `TrustManifest` that determines whether a tool can be called (e.g., Tool X requires `Trust > 0.8`).

## Open Questions

- **Token Signing**: Should we use local HMAC with a per-service secret or a centralized KMS for Capability Token signing? (Proposed: Local HMAC for latency, KMS for rotation).
- **Failure Mode**: For a high-risk enterprise tool, should we "Fail Closed" (error out) if the classifier is uncertain, even if the user query is benign?

## Verification Plan

### Adversarial Testing
- **Token Forgery**: Attempt to call a tool with a modified or expired token.
- **Parameter Injection**: Attempt to bypass constraint checks inside a valid tool call.
- **Deep Injection**: Test if a "high trust" RAG document can be combined with a "low trust" document to trick the model into a privileged plan.

### Performance Benchmarking
- Measure latency overhead of the 3-layer sanitization vs. baseline.
