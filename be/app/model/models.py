"""Pydantic models for the Model Provider domain."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ModelProviderPO(BaseModel):
    """Persistent object representing a model provider configuration.

    Attributes:
        id: Unique identifier (UUID hex).
        name: Human-readable provider name (e.g. "My Bedrock", "GPT-4o").
        type: Provider backend type — one of ``bedrock``, ``openai``, ``ollama``, ``anthropic``, ``custom``.
        config: Provider-specific configuration (api_key, base_url, region, etc.).
        models: List of model IDs available through this provider.
        is_default: Whether this is the default provider for new agents.
        status: Connection status — ``active``, ``inactive``, ``error``, ``unknown``.
        created_at: ISO-8601 creation timestamp.
        updated_at: ISO-8601 last-update timestamp.
    """

    id: str = ""
    name: str
    type: str  # bedrock | openai | ollama | anthropic | custom
    config: Dict = Field(default_factory=dict)
    models: List[str] = Field(default_factory=list)
    is_default: bool = False
    status: str = "unknown"
    created_at: str = ""
    updated_at: str = ""
