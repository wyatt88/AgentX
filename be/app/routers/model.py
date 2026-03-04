"""Model provider management API routes.

Provides endpoints for CRUD of model providers, connection testing,
and aggregated model listing across all active providers.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..model.models import ModelProviderPO
from ..model.service import ModelProviderService


provider_service = ModelProviderService()

router = APIRouter(
    prefix="/model",
    tags=["model"],
    responses={404: {"description": "Not found"}},
)


# ------------------------------------------------------------------
# Provider CRUD
# ------------------------------------------------------------------

@router.get("/providers")
def list_providers() -> list[ModelProviderPO]:
    """List all registered model providers."""
    return provider_service.list_providers()


@router.get("/provider/{provider_id}")
def get_provider(provider_id: str) -> ModelProviderPO:
    """Get a single model provider by ID.

    :param provider_id: The ID of the model provider.
    :return: Provider details.
    """
    provider = provider_service.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
    return provider


@router.post("/provider")
async def create_provider(request: Request) -> ModelProviderPO:
    """Create a new model provider.

    :return: The newly created provider with generated ``id`` and timestamps.
    """
    data = await request.json()
    provider = ModelProviderPO(
        name=data.get("name", ""),
        type=data.get("type", ""),
        config=data.get("config", {}),
        models=data.get("models", []),
        is_default=data.get("is_default", False),
        status=data.get("status", "unknown"),
    )
    created = provider_service.create_provider(provider)
    return created


@router.put("/provider/{provider_id}")
async def update_provider(provider_id: str, request: Request) -> ModelProviderPO:
    """Partially update an existing model provider.

    :param provider_id: The ID of the provider to update.
    :return: The updated provider record.
    """
    data = await request.json()
    updated = provider_service.update_provider(provider_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
    return updated


@router.delete("/provider/{provider_id}")
def delete_provider(provider_id: str) -> dict:
    """Delete a model provider by ID.

    :param provider_id: The ID of the provider to delete.
    :return: Deletion confirmation.
    """
    success = provider_service.delete_provider(provider_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete provider")
    return {"deleted": True, "id": provider_id}


# ------------------------------------------------------------------
# Connection testing
# ------------------------------------------------------------------

@router.post("/provider/{provider_id}/test")
def test_provider_connection(provider_id: str) -> dict:
    """Test connectivity to a model provider.

    Dispatches to provider-type-specific logic (bedrock, openai, ollama, etc.).

    :param provider_id: The ID of the provider to test.
    :return: Test result with ``status`` (``ok`` | ``error``) and details.
    """
    provider = provider_service.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
    result = provider_service.test_connection(provider)

    # If test succeeded, update status to active; otherwise error
    new_status = "active" if result.get("status") == "ok" else "error"
    provider_service.update_provider(provider_id, {"status": new_status})

    return result


# ------------------------------------------------------------------
# Aggregated models
# ------------------------------------------------------------------

@router.get("/available-models")
def list_available_models() -> list[dict]:
    """Aggregate models from all active providers.

    :return: List of objects with ``provider_id``, ``provider_name``,
             ``provider_type``, and ``models``.
    """
    return provider_service.list_available_models()
