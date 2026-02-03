#!/usr/bin/env python3
"""
Unibase AIP Skill — CLI only.

Usage: python scripts/index.py <tool> [params...]
  call_agent "<agent_handle>" "<objective>"
  stream_agent "<agent_handle>" "<objective>"
  auto_route "<objective>"
  health_check
  list_agents [limit] [offset]
  get_agent_info "<agent_id>"
  list_runs [limit] [offset]
  get_run_details "<run_id>"
  get_agent_price "<agent_id>"
  list_agent_prices [limit] [offset]
  register_agent "<agent_config_json>"
  unregister_agent "<agent_id>"
  register_user [email]
  list_users [limit] [offset]

Requires env (or .env): AIP_ENDPOINT, USER_WALLET_ADDRESS, MEMBASE_ACCOUNT (optional), MEMBASE_SECRET_KEY (optional)
Output: single JSON value to stdout. On error: {"error":"message"} and exit 1.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path to import aip_sdk
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from aip_sdk import AsyncAIPClient
except ImportError:
    # If aip_sdk is not installed, try to use the cloned SDK
    sdk_path = parent_dir / "unibase-aip-sdk"
    if sdk_path.exists():
        sys.path.insert(0, str(sdk_path))
        from aip_sdk import AsyncAIPClient
    else:
        print(json.dumps({"error": "aip_sdk not found. Please install with: pip install -e . or clone the SDK"}))
        sys.exit(1)


def out(data: Any) -> None:
    """Output JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False))


def cli_err(message: str) -> None:
    """Output error JSON and exit."""
    out({"error": message})
    sys.exit(1)


def get_config() -> Dict[str, str]:
    """Get configuration from environment variables."""
    # Try to load .env file if it exists
    env_file = parent_dir / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())

    aip_endpoint = os.environ.get("AIP_ENDPOINT", "http://api.aip.unibase.com")
    user_wallet = os.environ.get("USER_WALLET_ADDRESS")

    if not user_wallet:
        cli_err("Missing env: set USER_WALLET_ADDRESS")

    return {
        "aip_endpoint": aip_endpoint,
        "user_wallet": user_wallet,
        "membase_account": os.environ.get("MEMBASE_ACCOUNT"),
        "membase_secret_key": os.environ.get("MEMBASE_SECRET_KEY"),
    }


async def call_agent(agent_handle: str, objective: str) -> Dict[str, Any]:
    """Call a specific agent with an objective."""
    config = get_config()
    user_id = f"user:{config['user_wallet']}"

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        result = await client.run(
            objective=objective,
            agent=agent_handle,
            user_id=user_id,
            timeout=60.0,
        )

        return {
            "success": result.success,
            "status": result.status,
            "output": result.output,
            "agent": agent_handle,
            "objective": objective,
        }


async def stream_agent(agent_handle: str, objective: str) -> List[Dict[str, Any]]:
    """Call an agent and stream real-time events."""
    config = get_config()
    user_id = f"user:{config['user_wallet']}"

    events = []

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        async for event in client.run_stream(
            objective=objective,
            agent=agent_handle,
            user_id=user_id,
        ):
            event_data = {
                "event_type": event.event_type,
                "payload": event.payload,
            }
            events.append(event_data)

            # Break on completion or error
            if event.event_type in ("run_completed", "run_error"):
                break

    return events


async def auto_route(objective: str) -> Dict[str, Any]:
    """Let AIP platform automatically select the best agent."""
    config = get_config()
    user_id = f"user:{config['user_wallet']}"

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        result = await client.run(
            objective=objective,
            user_id=user_id,
            timeout=60.0,
        )

        return {
            "success": result.success,
            "status": result.status,
            "output": result.output,
            "objective": objective,
            "routed": True,
        }


async def health_check() -> Dict[str, Any]:
    """Check if AIP platform is available."""
    config = get_config()

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        is_healthy = await client.health_check()

        return {
            "healthy": is_healthy,
            "endpoint": config["aip_endpoint"],
        }


async def list_agents(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """List agents owned by the current user.

    Note: This lists agents registered by the user, not all available agents.
    To call an agent, you need to know its handle (e.g., 'weather_public', 'calculator_private').
    """
    config = get_config()
    user_id = f"user:{config['user_wallet']}"

    try:
        async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
            response = await client.list_user_agents(user_id, limit=limit, offset=offset)

            agents = []
            for agent in response.items:
                agents.append({
                    "agent_id": agent.agent_id,
                    "handle": agent.handle,
                    "name": agent.name,
                    "description": agent.description,
                    "price": agent.price,
                    "capabilities": agent.capabilities,
                    "on_chain": agent.on_chain,
                    "identity_address": agent.identity_address,
                })

            return {
                "agents": agents,
                "total": response.total,
                "limit": response.limit,
                "offset": response.offset,
            }
    except Exception as e:
        # If this endpoint is not available, return helpful message
        error_msg = str(e)
        if "502" in error_msg or "404" in error_msg:
            return {
                "agents": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "note": "Agent discovery endpoint not available. Use call_agent with known handles like 'weather_public' or 'calculator_private'."
            }
        raise


async def get_agent_info(agent_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific agent."""
    config = get_config()
    user_id = f"user:{config['user_wallet']}"

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        agent = await client.get_agent(user_id, agent_id)

        if not agent:
            cli_err(f"Agent not found: {agent_id}")

        return {
            "agent_id": agent.agent_id,
            "handle": agent.handle,
            "name": agent.name,
            "description": agent.description,
            "price": agent.price,
            "capabilities": agent.capabilities,
            "skills": agent.skills,
            "metadata": agent.metadata,
            "endpoint_url": agent.endpoint_url,
            "on_chain": agent.on_chain,
            "identity_address": agent.identity_address,
        }


async def list_runs(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """List task execution history."""
    config = get_config()
    user_id = f"user:{config['user_wallet']}"

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        response = await client.list_user_runs(user_id, limit=limit, offset=offset)

        return {
            "runs": response.items,
            "total": response.total,
            "limit": response.limit,
            "offset": response.offset,
        }


async def get_run_details(run_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific run including events and payments."""
    config = get_config()

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        events = await client.get_run_events(run_id)
        payments = await client.get_run_payments(run_id)

        return {
            "run_id": run_id,
            "events": events,
            "payments": payments,
        }


async def get_agent_price(agent_id: str) -> Dict[str, Any]:
    """Get pricing information for a specific agent."""
    config = get_config()
    user_id = f"user:{config['user_wallet']}"

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        price_info = await client.get_agent_price(user_id, agent_id)

        return {
            "agent_id": price_info.identifier,
            "amount": price_info.amount,
            "currency": price_info.currency,
            "metadata": price_info.metadata,
        }


async def list_agent_prices(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """List pricing for all agents."""
    config = get_config()

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        response = await client.list_agent_prices(limit=limit, offset=offset)

        prices = []
        for price in response.items:
            prices.append({
                "agent_id": price.identifier,
                "amount": price.amount,
                "currency": price.currency,
                "metadata": price.metadata,
            })

        return {
            "prices": prices,
            "total": response.total,
            "limit": response.limit,
            "offset": response.offset,
        }


async def register_agent(agent_config_json: str) -> Dict[str, Any]:
    """Register a new agent."""
    config = get_config()
    user_id = f"user:{config['user_wallet']}"

    try:
        agent_config = json.loads(agent_config_json)
    except json.JSONDecodeError as e:
        cli_err(f"Invalid JSON: {e}")

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        result = await client.register_agent(user_id, agent_config)
        return result


async def unregister_agent(agent_id: str) -> Dict[str, Any]:
    """Unregister an agent."""
    config = get_config()
    user_id = f"user:{config['user_wallet']}"

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        result = await client.unregister_agent(user_id, agent_id)
        return result


async def register_user(email: str = None) -> Dict[str, Any]:
    """Register a new user."""
    config = get_config()
    wallet_address = config["user_wallet"]

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        result = await client.register_user(wallet_address, email=email)
        return result


async def list_users(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """List all registered users."""
    config = get_config()

    async with AsyncAIPClient(base_url=config["aip_endpoint"]) as client:
        response = await client.list_users(limit=limit, offset=offset)

        users = []
        for user in response.items:
            users.append({
                "user_id": user.user_id,
                "wallet_address": user.wallet_address,
                "email": user.email,
                "created_at": user.created_at,
            })

        return {
            "users": users,
            "total": response.total,
            "limit": response.limit,
            "offset": response.offset,
        }


# Tool handlers
TOOLS = {
    "call_agent": {
        "min_args": 2,
        "usage": 'call_agent "<agent_handle>" "<objective>"',
        "handler": lambda args: call_agent(args[0], args[1]),
    },
    "stream_agent": {
        "min_args": 2,
        "usage": 'stream_agent "<agent_handle>" "<objective>"',
        "handler": lambda args: stream_agent(args[0], args[1]),
    },
    "auto_route": {
        "min_args": 1,
        "usage": 'auto_route "<objective>"',
        "handler": lambda args: auto_route(args[0]),
    },
    "health_check": {
        "min_args": 0,
        "usage": "health_check",
        "handler": lambda args: health_check(),
    },
    "list_agents": {
        "min_args": 0,
        "usage": "list_agents [limit] [offset]",
        "handler": lambda args: list_agents(
            int(args[0]) if len(args) > 0 else 100,
            int(args[1]) if len(args) > 1 else 0
        ),
    },
    "get_agent_info": {
        "min_args": 1,
        "usage": 'get_agent_info "<agent_id>"',
        "handler": lambda args: get_agent_info(args[0]),
    },
    "list_runs": {
        "min_args": 0,
        "usage": "list_runs [limit] [offset]",
        "handler": lambda args: list_runs(
            int(args[0]) if len(args) > 0 else 100,
            int(args[1]) if len(args) > 1 else 0
        ),
    },
    "get_run_details": {
        "min_args": 1,
        "usage": 'get_run_details "<run_id>"',
        "handler": lambda args: get_run_details(args[0]),
    },
    "get_agent_price": {
        "min_args": 1,
        "usage": 'get_agent_price "<agent_id>"',
        "handler": lambda args: get_agent_price(args[0]),
    },
    "list_agent_prices": {
        "min_args": 0,
        "usage": "list_agent_prices [limit] [offset]",
        "handler": lambda args: list_agent_prices(
            int(args[0]) if len(args) > 0 else 100,
            int(args[1]) if len(args) > 1 else 0
        ),
    },
    "register_agent": {
        "min_args": 1,
        "usage": 'register_agent "<agent_config_json>"',
        "handler": lambda args: register_agent(args[0]),
    },
    "unregister_agent": {
        "min_args": 1,
        "usage": 'unregister_agent "<agent_id>"',
        "handler": lambda args: unregister_agent(args[0]),
    },
    "register_user": {
        "min_args": 0,
        "usage": "register_user [email]",
        "handler": lambda args: register_user(args[0] if len(args) > 0 else None),
    },
    "list_users": {
        "min_args": 0,
        "usage": "list_users [limit] [offset]",
        "handler": lambda args: list_users(
            int(args[0]) if len(args) > 0 else 100,
            int(args[1]) if len(args) > 1 else 0
        ),
    },
}


async def run_cli():
    """Run CLI tool."""
    if len(sys.argv) < 2:
        cli_err("Usage: " + " | ".join(t["usage"] for t in TOOLS.values()))

    tool = sys.argv[1]
    args = sys.argv[2:]

    if tool not in TOOLS:
        cli_err(f"Unknown tool: {tool}. Usage: " + " | ".join(t["usage"] for t in TOOLS.values()))

    tool_info = TOOLS[tool]

    if len(args) < tool_info["min_args"]:
        cli_err(f"Usage: {tool_info['usage']}")

    try:
        result = await tool_info["handler"](args)
        out(result)
    except Exception as e:
        cli_err(str(e))


if __name__ == "__main__":
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        cli_err("Interrupted by user")
    except Exception as e:
        cli_err(f"Unexpected error: {str(e)}")
