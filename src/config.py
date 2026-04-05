from typing import Dict, Any

# Example endpoint templates for the UI to "pull"
DEFAULT_ENDPOINTS = {
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "models": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"]
    },
    "custom": {
        "url": "http://localhost:11434/api/generate", # Default Ollama
        "models": ["llama3", "mistral"]
    }
}
