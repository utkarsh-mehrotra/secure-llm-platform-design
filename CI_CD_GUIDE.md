# CI/CD Implementation Guide: Secure LLM Platform

This guide outlines the professional CI/CD pipeline for the Secure LLM Platform, ensuring every commit is verified against our "Secure by Construction" principles.

## 🚀 Pipeline Workflow

### 1. Build & Lint (Fast Feedback)
- **Tooling**: `flake8` for linting, `mypy` for static typing, `black` for formatting.
- **Action**: Reject any commit that fails the standardized style and type checks.

### 2. Automated Security Scanning
- **Static Analysis (SAST)**: Run `bandit -r src/` to find common Python security pitfalls.
- **Dependency Scanning**: Run `safety check` or `snyk test` to ensure no vulnerable libraries are in `requirements.txt`.
- **Secret Detection**: Use `gitleaks` to prevent accidental commits of LLM API keys or the `MASTER_KEY`.

### 3. Verification & Adversarial Testing
- **Unit Tests**: Run `pytest tests/test_security.py`.
- **Adversarial Suite**: Run the specialized jailbreak benchmarking suite (e.g., against the `retrieved_data` channel).
- **Hardness Eval**: Use `DeepEval` to verify hallucination and toxicity scores.

### 4. Containerization & Push
- **Build**: Build the production Docker image.
- **Push**: Push to Amazon ECR (Elastic Container Registry) or GitHub Container Registry (GHCR).

### 5. Deployment (Blue/Green)
- **Environment**: AWS EKS (Kubernetes).
- **Strategy**: Blue/Green or Canary deployment to ensure zero downtime.
- **Secrets**: Inject the `MASTER_KEY` via **AWS Secrets Manager** at runtime.

---

## 🛠️ Sample GitHub Actions Workflow (`.github/workflows/main.yml`)

```yaml
name: Secure LLM CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run Security Tests
      run: pytest tests/test_security.py
    - name: Run Bandit Security Scan
      run: bandit -r src/

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to EKS
      run: |
        # Deployment logic here...
```

---

> [!IMPORTANT]
> **Blocking Pipeline**: Security tests MUST be blocking. If a unit test involving the **CapabilityToken** fails, the deployment must be immediately aborted.
