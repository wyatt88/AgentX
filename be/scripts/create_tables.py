#!/usr/bin/env python3
"""
DynamoDB Table Creation Script for AgentX

Creates **all** AgentX tables (both 1.0 and 2.0):

  1.0 tables (existing):
    - AgentTable:              PK = id
    - ChatRecordTable:         PK = id
    - HttpMCPTable:            PK = id
    - AgentScheduleTable:      PK = id

  2.0 tables (new):
    - WorkflowTable:           PK = id
    - WorkflowExecutionTable:  PK = id, GSI = workflow_id-index (workflow_id, started_at)
    - ModelProviderTable:      PK = id

Usage:
    python be/scripts/create_tables.py [--endpoint-url http://localhost:8000]
    python be/scripts/create_tables.py --verify   # verify tables exist & GSI active

The script is idempotent — existing tables are skipped.
"""

import sys
import os
import argparse
import boto3
from botocore.exceptions import ClientError

# ---------------------------------------------------------------------------
# Allow running from repo root:  python be/scripts/create_tables.py
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from be.app.utils.aws_config import get_aws_region
except ImportError:
    # Fallback when module structure is not on the path
    def get_aws_region() -> str:
        return os.environ.get("AWS_REGION", "us-west-2")


# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------

TABLE_DEFINITIONS = [
    # ── 1.0 tables ────────────────────────────────────────────────────────
    {
        "TableName": "AgentTable",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "ChatRecordTable",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "HttpMCPTable",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "AgentScheduleTable",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    # ── 2.0 tables ────────────────────────────────────────────────────────
    {
        "TableName": "WorkflowTable",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "WorkflowExecutionTable",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "workflow_id", "AttributeType": "S"},
            {"AttributeName": "started_at", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "workflow_id-index",
                "KeySchema": [
                    {"AttributeName": "workflow_id", "KeyType": "HASH"},
                    {"AttributeName": "started_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "ModelProviderTable",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
]


def create_table(dynamodb_client: boto3.client, table_def: dict) -> None:
    """Create a single DynamoDB table, skipping if it already exists."""
    table_name = table_def["TableName"]
    try:
        dynamodb_client.create_table(**table_def)
        print(f"  ✅  Created table: {table_name}")
        # Wait until the table is active
        waiter = dynamodb_client.get_waiter("table_exists")
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 2, "MaxAttempts": 30})
        print(f"      Table {table_name} is now ACTIVE")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  ⏭️  Table already exists: {table_name}")
        else:
            raise


def verify_tables(dynamodb_client: boto3.client) -> bool:
    """Verify all tables exist and GSIs are active.

    :param dynamodb_client: boto3 DynamoDB client
    :return: True if all tables and GSIs are healthy
    """
    all_ok = True
    for table_def in TABLE_DEFINITIONS:
        table_name = table_def["TableName"]
        try:
            desc = dynamodb_client.describe_table(TableName=table_name)
            status = desc["Table"]["TableStatus"]
            print(f"  {'✅' if status == 'ACTIVE' else '⚠️'}  {table_name}: {status}")
            if status != "ACTIVE":
                all_ok = False

            # Check GSIs
            gsi_list = desc["Table"].get("GlobalSecondaryIndexes", [])
            for gsi in gsi_list:
                gsi_name = gsi["IndexName"]
                gsi_status = gsi["IndexStatus"]
                print(f"      GSI {gsi_name}: {gsi_status}")
                if gsi_status != "ACTIVE":
                    all_ok = False
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ResourceNotFoundException":
                print(f"  ❌  {table_name}: NOT FOUND")
                all_ok = False
            else:
                raise
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Create AgentX DynamoDB tables")
    parser.add_argument(
        "--endpoint-url",
        default=None,
        help="Optional DynamoDB endpoint URL (e.g. http://localhost:8000 for DynamoDB Local)",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="AWS region (defaults to AWS_REGION env var or us-west-2)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify tables exist and GSIs are active (no creation)",
    )
    args = parser.parse_args()

    region = args.region or get_aws_region()
    client_kwargs: dict = {"region_name": region}
    if args.endpoint_url:
        client_kwargs["endpoint_url"] = args.endpoint_url

    dynamodb_client = boto3.client("dynamodb", **client_kwargs)

    if args.verify:
        print(f"🔍 Verifying AgentX DynamoDB tables in region={region}")
        print()
        ok = verify_tables(dynamodb_client)
        print()
        if ok:
            print("🎉 All tables verified — healthy!")
        else:
            print("⚠️  Some tables are missing or unhealthy.")
            sys.exit(1)
        return

    print(f"🚀 Creating AgentX DynamoDB tables in region={region}")
    if args.endpoint_url:
        print(f"   Using endpoint: {args.endpoint_url}")
    print()

    for table_def in TABLE_DEFINITIONS:
        create_table(dynamodb_client, table_def)

    print()
    print("🎉 All tables ready!")


if __name__ == "__main__":
    main()
