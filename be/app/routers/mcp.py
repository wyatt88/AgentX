"""MCP server management API routes.

Provides endpoints for CRUD, group listing, health checking, and
tool introspection of registered MCP servers.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..mcp.mcp import HttpMCPServer, MCPService


mcp_service = MCPService()

router = APIRouter(
    prefix="/mcp",
    tags=["mcp"],
    responses={404: {"description": "Not found"}}
)


# ------------------------------------------------------------------
# Existing endpoints
# ------------------------------------------------------------------

@router.get("/list")
def list_mcp_servers() -> list[HttpMCPServer]:
    """List all MCP servers."""
    return mcp_service.list_mcp_servers()


@router.get("/get/{server_id}")
def get_mcp_server(server_id: str) -> HttpMCPServer | None:
    """Get a specific MCP server by ID.

    :param server_id: The ID of the MCP server to retrieve.
    :return: Details of the specified MCP server.
    """
    return mcp_service.get_mcp_server(server_id)


@router.delete("/delete/{server_id}")
def delete_mcp_server(server_id: str) -> bool:
    """Delete a specific MCP server by ID.

    :param server_id: The ID of the MCP server to delete.
    :return: True if deletion was successful, False otherwise.
    """
    return mcp_service.delete_mcp_server(server_id)


@router.post("/createOrUpdate")
async def create_mcp_server(server: Request) -> HttpMCPServer:
    """Create or update an MCP server.

    :param server: The MCP server data to create or update.
    :return: Confirmation of MCP server creation or update.
    """
    server_data = await server.json()
    server = HttpMCPServer(
        id=server_data.get("id"),
        name=server_data.get("name"),
        desc=server_data.get("desc"),
        host=server_data.get("host"),
        group=server_data.get("group", "default"),
        status=server_data.get("status", "unknown"),
        tags=server_data.get("tags", []),
    )
    mcp_service.add_mcp_server(server)
    return server


# ------------------------------------------------------------------
# New endpoints — groups, update, health check, tools
# ------------------------------------------------------------------

@router.get("/groups")
def list_groups() -> dict:
    """Return all MCP servers aggregated by group.

    :return: ``{"groups": {"groupName": [server, ...], ...}}``
    """
    return mcp_service.list_groups()


@router.put("/update/{server_id}")
async def update_mcp_server(server_id: str, request: Request) -> dict:
    """Partially update an existing MCP server.

    :param server_id: The ID of the MCP server to update.
    :return: The updated server record.
    """
    data = await request.json()
    updated = mcp_service.update_server(server_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")
    return updated.model_dump()


@router.post("/health-check/{server_id}")
async def health_check(server_id: str) -> dict:
    """Run a health check on a single MCP server.

    Connects via the MCP protocol, lists tools, and updates the persisted
    status accordingly.

    :param server_id: The ID of the MCP server to check.
    :return: Health check result with status and tools info.
    """
    result = await mcp_service.health_check(server_id)
    return result


@router.post("/health-check-all")
async def health_check_all() -> dict:
    """Run health checks on **all** registered MCP servers.

    :return: ``{"results": {serverId: healthResult, ...}}``
    """
    servers = mcp_service.list_mcp_servers()
    results: dict[str, dict] = {}
    for server in servers:
        result = await mcp_service.health_check(server.id)
        results[server.id] = result
    return {"results": results}


@router.get("/tools/{server_id}")
async def get_server_tools(server_id: str) -> list[dict]:
    """Retrieve the list of tools exposed by an MCP server.

    :param server_id: The ID of the MCP server to query.
    :return: List of tool descriptors (name + description).
    """
    try:
        tools = await mcp_service.get_server_tools(server_id)
        return tools
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
