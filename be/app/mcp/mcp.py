"""MCP Server data model and service layer.

Provides HttpMCPServer Pydantic model and MCPService for DynamoDB-backed
CRUD, group management, health checking, and tool introspection.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

import boto3
from boto3.dynamodb.conditions import Attr
from pydantic import BaseModel, Field

from ..utils.aws_config import get_aws_region


class HttpMCPServer(BaseModel):
    """Represents a registered HTTP-based MCP server."""

    id: str | None = None
    name: str
    desc: str
    host: str
    group: str = "default"
    status: str = "unknown"  # unknown | running | error
    health_check_at: str = ""
    tools_count: int = 0
    tags: List[str] = Field(default_factory=list)


class MCPService:
    """Service for managing MCP servers in DynamoDB.

    Supports CRUD operations, group-based listing, health checks,
    and remote tool introspection via the MCP protocol.
    """

    dynamodb_table_name = "HttpMCPTable"

    def __init__(self) -> None:
        aws_region = get_aws_region()
        self.dynamodb = boto3.resource('dynamodb', region_name=aws_region)

    # ------------------------------------------------------------------
    # Basic CRUD
    # ------------------------------------------------------------------

    def add_mcp_server(self, server: HttpMCPServer) -> None:
        """Persist (create or overwrite) an MCP server record."""
        if not server.id:
            server.id = uuid.uuid4().hex
        self.dynamodb.Table(self.dynamodb_table_name).put_item(
            Item={
                'id': server.id,
                'name': server.name,
                'desc': server.desc,
                'host': server.host,
                'group': server.group,
                'status': server.status,
                'health_check_at': server.health_check_at,
                'tools_count': server.tools_count,
                'tags': server.tags,
            }
        )

    def list_mcp_servers(self) -> list[HttpMCPServer]:
        """Return all registered MCP servers."""
        response = self.dynamodb.Table(self.dynamodb_table_name).scan()
        items = response.get('Items', [])
        self.mcp_servers = [HttpMCPServer.model_validate(item) for item in items]
        return self.mcp_servers

    def get_mcp_server(self, id: str) -> HttpMCPServer | None:
        """Retrieve a single MCP server by primary key."""
        response = self.dynamodb.Table(self.dynamodb_table_name).get_item(
            Key={'id': id}
        )
        item = response.get('Item')
        if item:
            return HttpMCPServer.model_validate(item)
        return None

    def delete_mcp_server(self, id: str) -> bool:
        """Delete an MCP server by primary key."""
        response = self.dynamodb.Table(self.dynamodb_table_name).delete_item(
            Key={'id': id}
        )
        return response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200

    def update_server(self, id: str, data: dict) -> HttpMCPServer | None:
        """Update an existing MCP server with partial data.

        Fetches the current record, merges *data* on top, then persists.

        :param id: Server primary key.
        :param data: Dictionary of fields to update.
        :return: The updated HttpMCPServer, or None if not found.
        """
        server = self.get_mcp_server(id)
        if not server:
            return None

        # Merge provided fields onto existing record
        update_dict = server.model_dump()
        update_dict.update(data)
        updated_server = HttpMCPServer.model_validate(update_dict)
        self.add_mcp_server(updated_server)
        return updated_server

    # ------------------------------------------------------------------
    # Group helpers
    # ------------------------------------------------------------------

    def list_groups(self) -> dict:
        """Return MCP servers aggregated by group.

        :return: ``{"groups": {"default": [server, ...], ...}}``
        """
        servers = self.list_mcp_servers()
        groups: dict[str, list[dict]] = {}
        for s in servers:
            groups.setdefault(s.group, []).append(s.model_dump())
        return {"groups": groups}

    def list_by_group(self, group: str) -> list[HttpMCPServer]:
        """Return all MCP servers belonging to *group*."""
        response = self.dynamodb.Table(self.dynamodb_table_name).scan(
            FilterExpression=Attr('group').eq(group)
        )
        items = response.get('Items', [])
        return [HttpMCPServer.model_validate(item) for item in items]

    # ------------------------------------------------------------------
    # Health check & tool introspection
    # ------------------------------------------------------------------

    async def health_check(self, server_id: str) -> dict:
        """Probe an MCP server's health by connecting and listing tools.

        Updates the persisted record with new status, tools_count, and
        health_check_at timestamp.

        :param server_id: Primary key of the server to check.
        :return: Dict with ``status``, ``tools``/``tools_count`` on success,
                 or ``status`` + ``error`` on failure.
        """
        from strands.tools.mcp.mcp_client import MCPClient
        from mcp.client.streamable_http import streamablehttp_client

        server = self.get_mcp_server(server_id)
        if not server:
            return {"status": "error", "error": f"Server {server_id} not found"}

        mcp_client: Optional[MCPClient] = None
        try:
            server_host = server.host
            mcp_client = MCPClient(lambda: streamablehttp_client(server_host))
            mcp_client = mcp_client.start()
            tools = mcp_client.list_tools_sync()

            now_str = datetime.now(timezone.utc).isoformat()
            self.update_server(server_id, {
                "status": "running",
                "tools_count": len(tools),
                "health_check_at": now_str,
            })

            tool_list = [{"name": t.name, "description": t.description} for t in tools]
            return {"status": "running", "tools": tool_list, "tools_count": len(tools)}
        except Exception as e:
            now_str = datetime.now(timezone.utc).isoformat()
            self.update_server(server_id, {
                "status": "error",
                "health_check_at": now_str,
            })
            return {"status": "error", "error": str(e)}
        finally:
            if mcp_client is not None:
                try:
                    mcp_client.stop()
                except Exception:
                    pass

    async def get_server_tools(self, server_id: str) -> list[dict]:
        """Retrieve the list of tools exposed by an MCP server.

        :param server_id: Primary key of the server to query.
        :return: List of dicts with ``name`` and ``description``.
        :raises ValueError: If the server is not found.
        """
        from strands.tools.mcp.mcp_client import MCPClient
        from mcp.client.streamable_http import streamablehttp_client

        server = self.get_mcp_server(server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")

        mcp_client: Optional[MCPClient] = None
        try:
            server_host = server.host
            mcp_client = MCPClient(lambda: streamablehttp_client(server_host))
            mcp_client = mcp_client.start()
            tools = mcp_client.list_tools_sync()
            return [{"name": t.name, "description": t.description} for t in tools]
        finally:
            if mcp_client is not None:
                try:
                    mcp_client.stop()
                except Exception:
                    pass
