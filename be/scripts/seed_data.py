#!/usr/bin/env python3
"""
Seed Data Script for AgentX 2.0

Creates sample data so the frontend has something to display:
  - 1 Bedrock ModelProvider (is_default=True)
  - 1 OpenAI ModelProvider
  - 1 example Workflow (Start → Agent → End)

Usage:
    python3 be/scripts/seed_data.py [--endpoint-url http://localhost:8000]
    python3 be/scripts/seed_data.py --clear   # delete seed data first

The script is idempotent — it checks for existing items before creating.
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

# ---------------------------------------------------------------------------
# Allow running from repo root:  python3 be/scripts/seed_data.py
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from be.app.utils.aws_config import get_aws_region
except ImportError:
    def get_aws_region() -> str:
        return os.environ.get("AWS_REGION", "us-west-2")


# ---------------------------------------------------------------------------
# Seed IDs (deterministic so re-runs are idempotent)
# ---------------------------------------------------------------------------
BEDROCK_PROVIDER_ID = "seed-bedrock-provider-001"
OPENAI_PROVIDER_ID = "seed-openai-provider-002"
SAMPLE_WORKFLOW_ID = "seed-workflow-demo-001"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Seed definitions
# ---------------------------------------------------------------------------

def bedrock_provider(ts: str) -> dict:
    return {
        "id": BEDROCK_PROVIDER_ID,
        "name": "AWS Bedrock (Default)",
        "type": "bedrock",
        "config": {
            "region": "us-east-1",
            "description": "Default Bedrock provider — uses instance IAM role.",
        },
        "models": [
            "us.anthropic.claude-sonnet-4-20250514-v1:0",
            "us.anthropic.claude-3-5-haiku-20241022-v1:0",
            "us.amazon.nova-pro-v1:0",
            "us.amazon.nova-lite-v1:0",
        ],
        "is_default": True,
        "status": "active",
        "created_at": ts,
        "updated_at": ts,
    }


def openai_provider(ts: str) -> dict:
    return {
        "id": OPENAI_PROVIDER_ID,
        "name": "OpenAI",
        "type": "openai",
        "config": {
            "base_url": "https://api.openai.com/v1",
            "api_key": "<YOUR_OPENAI_API_KEY>",
            "description": "OpenAI API — replace api_key with a real key.",
        },
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
        ],
        "is_default": False,
        "status": "inactive",
        "created_at": ts,
        "updated_at": ts,
    }


def sample_workflow(ts: str) -> dict:
    """A minimal Start → Agent → End workflow."""
    definition = {
        "nodes": [
            {
                "id": "node-start",
                "type": "start",
                "position": {"x": 100, "y": 200},
                "data": {"label": "Start"},
            },
            {
                "id": "node-agent",
                "type": "agent",
                "position": {"x": 400, "y": 200},
                "data": {
                    "label": "Demo Agent",
                    "agent_id": "",
                    "system_prompt": "You are a helpful assistant.",
                    "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
                },
            },
            {
                "id": "node-end",
                "type": "end",
                "position": {"x": 700, "y": 200},
                "data": {"label": "End"},
            },
        ],
        "edges": [
            {"id": "e-start-agent", "source": "node-start", "target": "node-agent"},
            {"id": "e-agent-end", "source": "node-agent", "target": "node-end"},
        ],
    }

    return {
        "id": SAMPLE_WORKFLOW_ID,
        "name": "Demo: Start → Agent → End",
        "description": "A simple 3-node demonstration workflow created by seed script.",
        "status": "draft",
        "definition": json.dumps(definition, ensure_ascii=False),
        "trigger_type": "manual",
        "trigger_config": "{}",
        "created_at": ts,
        "updated_at": ts,
    }


# ---------------------------------------------------------------------------
# DynamoDB helpers
# ---------------------------------------------------------------------------

def item_exists(table, key: dict) -> bool:
    resp = table.get_item(Key=key)
    return "Item" in resp


def put_if_absent(table, item: dict, key_field: str = "id") -> bool:
    """Put item only if it doesn't already exist. Returns True if created."""
    key = {key_field: item[key_field]}
    if item_exists(table, key):
        print(f"  ⏭️  Already exists: {item.get('name', item[key_field])}")
        return False
    table.put_item(Item=item)
    print(f"  ✅  Created: {item.get('name', item[key_field])}")
    return True


def delete_seed_data(dynamodb) -> None:
    """Remove all seed data items."""
    print("🗑️  Clearing seed data...")

    provider_table = dynamodb.Table("ModelProviderTable")
    for pid in [BEDROCK_PROVIDER_ID, OPENAI_PROVIDER_ID]:
        try:
            provider_table.delete_item(Key={"id": pid})
            print(f"  Deleted provider: {pid}")
        except ClientError:
            pass

    wf_table = dynamodb.Table("WorkflowTable")
    try:
        wf_table.delete_item(Key={"id": SAMPLE_WORKFLOW_ID})
        print(f"  Deleted workflow: {SAMPLE_WORKFLOW_ID}")
    except ClientError:
        pass

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Seed AgentX demo data")
    parser.add_argument(
        "--endpoint-url",
        default=None,
        help="Optional DynamoDB endpoint (e.g. http://localhost:8000 for local)",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="AWS region (defaults to AWS_REGION env or us-west-2)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing seed data before inserting",
    )
    args = parser.parse_args()

    region = args.region or get_aws_region()
    resource_kwargs: dict = {"region_name": region}
    if args.endpoint_url:
        resource_kwargs["endpoint_url"] = args.endpoint_url

    dynamodb = boto3.resource("dynamodb", **resource_kwargs)
    ts = now_iso()

    print(f"🌱 Seeding AgentX demo data  (region={region})")
    if args.endpoint_url:
        print(f"   Endpoint: {args.endpoint_url}")
    print()

    if args.clear:
        delete_seed_data(dynamodb)

    # ── Model Providers ───────────────────────────────────────────────
    print("📦 Model Providers")
    provider_table = dynamodb.Table("ModelProviderTable")
    put_if_absent(provider_table, bedrock_provider(ts))
    put_if_absent(provider_table, openai_provider(ts))
    print()

    # ── Workflows ─────────────────────────────────────────────────────
    print("🔀 Workflows")
    wf_table = dynamodb.Table("WorkflowTable")
    put_if_absent(wf_table, sample_workflow(ts))
    print()

    print("🎉 Seed data ready!")


if __name__ == "__main__":
    main()
