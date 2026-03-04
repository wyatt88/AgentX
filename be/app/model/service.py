"""Model Provider service layer.

Provides ModelProviderService for DynamoDB-backed CRUD of model provider
configurations, connection testing, and aggregated model listing.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import boto3
import requests
from boto3.dynamodb.conditions import Attr

from .models import ModelProviderPO
from ..utils.aws_config import get_aws_region


class ModelProviderService:
    """Service for managing model providers in DynamoDB.

    Supports full CRUD, connection testing for different provider types
    (bedrock, openai, ollama, anthropic, custom), and aggregation of
    available models across all active providers.
    """

    dynamodb_table_name = "ModelProviderTable"

    def __init__(self) -> None:
        aws_region = get_aws_region()
        self.dynamodb = boto3.resource('dynamodb', region_name=aws_region)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    def create_provider(self, provider: ModelProviderPO) -> ModelProviderPO:
        """Create a new model provider.

        Auto-generates ``id``, ``created_at``, and ``updated_at`` if absent.

        :param provider: The provider to persist.
        :return: The persisted provider with generated fields.
        """
        if not provider.id:
            provider.id = uuid.uuid4().hex
        now_str = datetime.now(timezone.utc).isoformat()
        if not provider.created_at:
            provider.created_at = now_str
        provider.updated_at = now_str

        self._put_provider(provider)
        return provider

    def get_provider(self, provider_id: str) -> Optional[ModelProviderPO]:
        """Retrieve a single model provider by primary key.

        :param provider_id: The provider ID.
        :return: The provider, or ``None`` if not found.
        """
        response = self.dynamodb.Table(self.dynamodb_table_name).get_item(
            Key={'id': provider_id}
        )
        item = response.get('Item')
        if item:
            return self._item_to_provider(item)
        return None

    def list_providers(self) -> List[ModelProviderPO]:
        """Return all registered model providers."""
        response = self.dynamodb.Table(self.dynamodb_table_name).scan()
        items = response.get('Items', [])
        return [self._item_to_provider(item) for item in items]

    def update_provider(self, provider_id: str, data: dict) -> Optional[ModelProviderPO]:
        """Partially update an existing provider.

        Fetches the current record, merges *data* on top, then persists.

        :param provider_id: Provider primary key.
        :param data: Dictionary of fields to update.
        :return: The updated provider, or ``None`` if not found.
        """
        existing = self.get_provider(provider_id)
        if not existing:
            return None

        update_dict = existing.model_dump()
        update_dict.update(data)
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()

        updated = ModelProviderPO.model_validate(update_dict)
        self._put_provider(updated)
        return updated

    def delete_provider(self, provider_id: str) -> bool:
        """Delete a model provider by primary key.

        :param provider_id: Provider primary key.
        :return: ``True`` if DynamoDB returned HTTP 200.
        """
        response = self.dynamodb.Table(self.dynamodb_table_name).delete_item(
            Key={'id': provider_id}
        )
        return response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200

    # ------------------------------------------------------------------
    # Connection testing
    # ------------------------------------------------------------------

    def test_connection(self, provider: ModelProviderPO) -> dict:
        """Test connectivity to a model provider.

        Dispatches to provider-specific logic based on ``provider.type``:

        - **bedrock** — calls ``boto3 bedrock-runtime list_foundation_models``
        - **openai** / **anthropic** / **custom** — ``GET <base_url>/models``
        - **ollama** — ``GET <base_url>/api/tags``

        :param provider: The provider to test.
        :return: Dict with ``status`` (``ok`` | ``error``) and optional details.
        """
        provider_type = provider.type.lower()

        try:
            if provider_type == "bedrock":
                return self._test_bedrock(provider)
            elif provider_type in ("openai", "anthropic", "custom"):
                return self._test_openai_compatible(provider)
            elif provider_type == "ollama":
                return self._test_ollama(provider)
            else:
                return {"status": "error", "error": f"Unsupported provider type: {provider_type}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ------------------------------------------------------------------
    # Model aggregation
    # ------------------------------------------------------------------

    def list_available_models(self) -> List[dict]:
        """Aggregate models from all active providers.

        :return: List of dicts with ``provider_id``, ``provider_name``,
                 ``provider_type``, and ``models``.
        """
        providers = self.list_providers()
        result: List[dict] = []
        for p in providers:
            if p.status != "active":
                continue
            result.append({
                "provider_id": p.id,
                "provider_name": p.name,
                "provider_type": p.type,
                "models": p.models,
            })
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _put_provider(self, provider: ModelProviderPO) -> None:
        """Persist a provider to DynamoDB."""
        item: Dict = {
            'id': provider.id,
            'name': provider.name,
            'type': provider.type,
            'config': provider.config,
            'models': provider.models,
            'is_default': provider.is_default,
            'status': provider.status,
            'created_at': provider.created_at,
            'updated_at': provider.updated_at,
        }
        self.dynamodb.Table(self.dynamodb_table_name).put_item(Item=item)

    @staticmethod
    def _item_to_provider(item: dict) -> ModelProviderPO:
        """Map a DynamoDB item to a ModelProviderPO."""
        return ModelProviderPO(
            id=item.get('id', ''),
            name=item.get('name', ''),
            type=item.get('type', ''),
            config=item.get('config', {}),
            models=item.get('models', []),
            is_default=item.get('is_default', False),
            status=item.get('status', 'unknown'),
            created_at=item.get('created_at', ''),
            updated_at=item.get('updated_at', ''),
        )

    @staticmethod
    def _test_bedrock(provider: ModelProviderPO) -> dict:
        """Test AWS Bedrock connectivity.

        Uses ``bedrock`` (not ``bedrock-runtime``) to call
        ``list_foundation_models`` as a lightweight probe.
        """
        region = provider.config.get('region', get_aws_region())
        client = boto3.client('bedrock', region_name=region)
        response = client.list_foundation_models(byOutputModality='TEXT')
        model_count = len(response.get('modelSummaries', []))
        return {
            "status": "ok",
            "message": f"Bedrock connected successfully. {model_count} text models available.",
        }

    @staticmethod
    def _test_openai_compatible(provider: ModelProviderPO) -> dict:
        """Test OpenAI-compatible API connectivity (OpenAI, Anthropic, custom)."""
        base_url = provider.config.get('base_url', '').rstrip('/')
        api_key = provider.config.get('api_key', '')

        if not base_url:
            return {"status": "error", "error": "base_url is required in config"}

        headers: Dict[str, str] = {}
        if api_key:
            headers['Authorization'] = f"Bearer {api_key}"

        resp = requests.get(f"{base_url}/models", headers=headers, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        model_ids = [m.get('id', '') for m in data.get('data', [])] if isinstance(data, dict) else []
        return {
            "status": "ok",
            "message": f"Connected successfully. {len(model_ids)} models found.",
            "models": model_ids[:20],  # cap to avoid huge payloads
        }

    @staticmethod
    def _test_ollama(provider: ModelProviderPO) -> dict:
        """Test Ollama API connectivity."""
        base_url = provider.config.get('base_url', 'http://localhost:11434').rstrip('/')

        resp = requests.get(f"{base_url}/api/tags", timeout=10)
        resp.raise_for_status()

        data = resp.json()
        models = [m.get('name', '') for m in data.get('models', [])]
        return {
            "status": "ok",
            "message": f"Ollama connected successfully. {len(models)} models available.",
            "models": models,
        }
