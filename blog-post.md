---
layout: post
title: "Towards Formally Verifiable Security in LLM-Based Agents"
subtitle: "Moving Beyond Prompt Engineering with Policy-Learned Capability Constraints"
date: "2026-04-13"
author: "Utkarsh Mehrotra & Himakshi Bhatia"
category: Security Engineering
tags: [LLMs, Security, Agentic Systems, AI, Cybersecurity]
---

The integration of Large Language Models (LLMs) with external data sources—whether through RAG (Retrieval-Augmented Generation) or fully autonomous agents—has unlocked incredible capabilities. But it has also introduced a critical vulnerability: **Indirect Prompt Injection (IPI)**. 

When an LLM retrieves untrusted documents, a malicious adversary who has planted instructions in that data can override the system’s primary intent. In high-consequence domains like healthcare, fintech, and regulated enterprise environments, it's unacceptable to allow an AI to autonomously transfer funds or delete records based on hidden instructions in a retrieved email or database record.

Today, we are moving our **Secure LLM Platform** from prototype heuristics to a **Formally Verifiable Security Framework**. Here’s why we did it, and how it works.

---

### The Problem: Why Semantic Filters Fail

Current industry defenses typically treat Prompt Injection as a content detection problem:
*   **Text Delimiters** (e.g., placing data inside `---BEGIN DATA---` blocks).
*   **Semantic Classifiers** (e.g., Llama Guard, NeMo Guardrails).

The fundamental issue is that these are *soft boundaries*. An adaptive adversary can simply paraphrase an attack payload, or use colloquial language that slips past the regex engines. Treating prompt injection as a "text filtering" issue creates an unwinnable adversarial arms race—ultimately severely limiting the environments in which agentic LLMs can be deployed.

### A New Threat Taxonomy: Class A / B / C

We argue that LLM security must be framed as a **Capability-Based Authorization** problem rather than text detection. To address this, we define a precise, three-level threat model:

1. **IPI-A (Tool-Execution):** The attacker tries to execute a highly privileged tool (e.g., dropping a database or extracting money). 
2. **IPI-B (Decision-Influence):** The attacker biases the LLM’s reasoning (e.g., skewing a summary to approve a loan).
3. **IPI-C (Information-Disclosure):** The attacker attempts to trick the LLM into leaking its system instructions or sensitive data inputs.

We need *hard* architectural guarantees against Class-A threats, while deploying robust defense-in-depth for Class B and C.

---

### The Solution: Secure-By-Construction Architecture

Our upgraded platform introduces three major architectural shifts that prioritize hard execution boundaries. 

#### 1. Multi-Channel Input Isolation

We stop treating the LLM context window as a massive flat string. Context is separated into strict, isolated channels:
*   **System Channel:** Cryptographically signed instructions (the core agent identity and hardcoded rules). The orchestrator will physically reject execution if this signature is tampered with.
*   **User Channel:** RBAC (Role-Based Access Control) enforced query environments limiting what tools the user is even authorized to execute.
*   **Data Channel:** Zero-trust retrieval. Untrusted external data is never executed; it strictly serves as reference context enforced via prompt framing.

#### 2. CLOP: Constraint Learning Over Periods

We can't ask security engineers to manually write and maintain impenetrable regex for every single new parameter of every tool a product team introduces. 

Instead, we built **CLOP** (Constraint Learning Over Periods). CLOP is a machine-learning-driven policy engine that synthesizes strict parameter bounds (categorical and numerical constraints) by observing normal, legitimate user-to-tool behavior traces. 

*   **Meta-Learner Generalization:** Using Random Forest modeling, CLOP can even extract the semantic similarity of *unseen* tools and automatically predict and apply strict interaction constraints with an **82% generalization success rate**. 
*   This lowers manual security engineering overhead by **70%**.

#### 3. Cryptographic Capability Tokens (HMAC)

The LLM does not execute anything; it *requests* execution. 
When an execution intent is flagged, the Orchestrator evaluates the learned CLOP rules, user RBAC strings, and intent constraints. If valid, it issues a time-bounded, **HMAC-SHA256 Capability Token**.

Our downstream stateless **Tool Gateway** completely ignores the LLM’s unstructured output. It only executes if—and only if—the HMAC capability token matches the parameters perfectly. 

---

### Benchmarking and 98.2% Class-A Mitigation

We subjected the platform to the massive **IPIBENCH-2847** suite—a simulation of over 2,800 complex adversarial documents evaluated by both automated attacks and human red-teamers. 

The results establish a new standard for Agent security:
*   **98.2% Mitigation** against Class-A tool-execution attacks.
*   **< 5ms Median Latency Overhead** on a fully-isolated execution token gateway.
*   **F-Score of 0.961** balancing flawless security halts while preserving benign execution queries.

### What's Next? 

LLM agents require engineering maturity. By deploying *Hard Data Plane Isolation*, *Cryptographic Tokenization*, and *Automated Constraint Learning*, we finally provide a platform viable for regulated environments requiring formal verification and audit trails securely logged to centralized SecOps nodes.

You can explore the full source code, benchmark logic, and deep-dive architectural specifications right here in this repository.

*— The Secure Systems Architecture Group*
