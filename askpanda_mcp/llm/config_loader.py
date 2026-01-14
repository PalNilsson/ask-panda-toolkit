"""Helper to build LLM model registry from application configuration."""

from __future__ import annotations

from askpanda_mcp.config import Config
from askpanda_mcp.llm.registry import ModelRegistry
from askpanda_mcp.llm.types import ModelSpec


def build_model_registry_from_config(config: Config) -> ModelRegistry:
    """Builds a ModelRegistry from application configuration.

    This helper centralizes how LLM profiles are defined so that:
    - tools never reference providers directly
    - plugins can later override or extend profiles
    - config format can evolve (env -> YAML) without touching callers

    Args:
        config: Global application configuration.

    Returns:
        A ModelRegistry populated with standard profiles.
    """
    profiles: dict[str, ModelSpec] = {
        "default": ModelSpec(
            provider=config.LLM_DEFAULT_PROVIDER,
            model=config.LLM_DEFAULT_MODEL,
        ),
        "fast": ModelSpec(
            provider=config.LLM_FAST_PROVIDER,
            model=config.LLM_FAST_MODEL,
        ),
        "reasoning": ModelSpec(
            provider=config.LLM_REASONING_PROVIDER,
            model=config.LLM_REASONING_MODEL,
        ),
    }

    # Optional OpenAI-compatible override for local / self-hosted models
    # This enables Llama/Mistral via vLLM, Ollama, LM Studio, etc.
    if config.OPENAI_COMPAT_BASE_URL:
        for spec in profiles.values():
            if spec.provider == "openai_compat":
                spec.extra = spec.extra or {}
                spec.extra["base_url"] = config.OPENAI_COMPAT_BASE_URL

    return ModelRegistry(profiles=profiles)
