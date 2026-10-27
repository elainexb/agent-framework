"""The only place that knows how to connect to a model provider."""
from __future__ import annotations
import os
from .config import AgentSpec


def make_model(spec: AgentSpec):
    if spec.provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=spec.model,
            temperature=spec.temperature,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    if spec.provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("Set OPENAI_API_KEY in .env before using the OpenAI provider")
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise RuntimeError("Install optional dependency: pip install -e '.[openai]'") from exc
        return ChatOpenAI(model=spec.model, temperature=spec.temperature)
    raise ValueError(f"Unsupported model provider: {spec.provider}")
