# Secure LLM Platform | Full-Stack Gateway & Research Reference

A production-grade, security-hardened LLM platform designed to mitigate prompt injection through **Data Plane Isolation** and **Capability-Based Security**.

## 🛡️ Core Security Features

*   **Multi-Channel Input Isolation**: Strictly separates `system`, `user`, and `retrieved (RAG)` data into isolated channels.
*   **HMAC-Signed Capability Tokens**: Every tool execution requires a short-lived, cryptographically signed token issued by the Control Plane.
*   **Three-Layer Sanitization Pipeline**:
    *   **L1 (Regex)**: Fast rejection of known prompt injection patterns.
    *   **L2 (Classifier)**: Probabilistic risk scoring for adversarial inputs.
    *   **L3 (Transformation)**: Neutralizes instructional content into passive descriptions.

## 🚀 Full-Stack Overview

### Backend (Python/FastAPI)
- **Dynamic Orchestrator**: Supports OpenAI, Anthropic, and Custom LLM providers.
- **Stateless Tokens**: Fast, HMAC-BASED verification with no database overhead.

### Frontend (React/Vite)
- **Trust-First UI**: Visualizes real-time `TrustScore` and sanitization status.
- **Glassmorphism Chat**: High-fidelity UI with thought-process transparency.

### Research & Certification
- **[paper.tex](file:///Users/utkarsh/Documents/secure-llm-platform/paper.tex)**: Formal research paper on the architecture.
- **[testing_requirements.md](file:///Users/utkarsh/Documents/secure-llm-platform/testing_requirements.md)**: Production-grade certification roadmap.

## 🛠️ Quick Start

### 1. One-Click Setup (Docker)
```bash
# Start the full-stack system
docker-compose up --build
```

### 2. Manual Setup
```bash
# Backend
pip install -r requirements.txt
uvicorn src.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

### 3. Verification
```bash
# Run security tests
pytest tests/test_security.py
```

## 📐 Architecture
The platform is built on the principle of **Secure-by-Construction**. By decoupling the **Control Plane** (Orchestrator) from the **Data Plane** (Untrusted RAG Data), we ensure that a compromised model cannot escalate privileges.

---
**Secure LLM Platform** - Built for Staff-level Security and Planet-scale Reliability.
