import json
import os
import requests
from tools.registry import registry

DISCORD_API_URL = "https://discord.com/api/v10"
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "")


def check_requirements() -> bool:
    """Check if Discord API is accessible (requires bot token)"""
    return bool(DISCORD_BOT_TOKEN)


def get_channel_messages(channel_id: str, limit: int = 10) -> str:
    """Get recent messages from a Discord channel"""
    try:
        if not DISCORD_BOT_TOKEN:
            return json.dumps({"error": "DISCORD_BOT_TOKEN not configured"})
        
        url = f"{DISCORD_API_URL}/channels/{channel_id}/messages"
        params = {"limit": min(limit, 100)}
        headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        messages = []
        for msg in data:
            messages.append({
                "id": msg.get("id"),
                "content": msg.get("content", "")[:200],
                "author": msg.get("author", {}).get("username"),
                "timestamp": msg.get("timestamp"),
                "attachments": len(msg.get("attachments", []))
            })
        
        return json.dumps({"channel_id": channel_id, "messages": messages})
    except Exception as e:
        return json.dumps({"error": str(e)})


def search_channel(channel_id: str, query: str, limit: int = 10) -> str:
    """Search for messages in a Discord channel"""
    try:
        if not DISCORD_BOT_TOKEN:
            return json.dumps({"error": "DISCORD_BOT_TOKEN not configured"})
        
        url = f"{DISCORD_API_URL}/channels/{channel_id}/messages"
        params = {"limit": min(limit, 100)}
        headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for msg in data:
            content = msg.get("content", "")
            if query.lower() in content.lower():
                results.append({
                    "id": msg.get("id"),
                    "content": content[:200],
                    "author": msg.get("author", {}).get("username"),
                    "timestamp": msg.get("timestamp")
                })
        
        return json.dumps({
            "channel_id": channel_id,
            "query": query,
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_guild_info(guild_id: str = None) -> str:
    """Get guild/server information"""
    try:
        if not DISCORD_BOT_TOKEN:
            return json.dumps({"error": "DISCORD_BOT_TOKEN not configured"})
        
        guild_id = guild_id or DISCORD_GUILD_ID
        if not guild_id:
            return json.dumps({"error": "DISCORD_GUILD_ID not configured"})
        
        url = f"{DISCORD_API_URL}/guilds/{guild_id}"
        headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "name": data.get("name"),
            "id": data.get("id"),
            "member_count": data.get("member_count"),
            "owner_id": data.get("owner_id")
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


registry.register(
    name="discord_channel_messages",
    toolset="social",
    schema={
        "name": "discord_channel_messages",
        "description": "Get recent messages from a Discord channel",
        "parameters": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "Channel ID"},
                "limit": {"type": "integer", "description": "Max messages", "default": 10}
            },
            "required": ["channel_id"]
        }
    },
    handler=lambda args, **kw: get_channel_messages(
        args.get("channel_id", ""),
        args.get("limit", 10)
    ),
    check_fn=check_requirements
)

registry.register(
    name="discord_search",
    toolset="social",
    schema={
        "name": "discord_search",
        "description": "Search messages in a Discord channel",
        "parameters": {
            "type": "object",
            "properties": {
                "channel_id": {"type": "string", "description": "Channel ID"},
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["channel_id", "query"]
        }
    },
    handler=lambda args, **kw: search_channel(
        args.get("channel_id", ""),
        args.get("query", ""),
        args.get("limit", 10)
    ),
    check_fn=check_requirements
)

registry.register(
    name="discord_guild_info",
    toolset="social",
    schema={
        "name": "discord_guild_info",
        "description": "Get Discord server/guild information",
        "parameters": {
            "type": "object",
            "properties": {
                "guild_id": {"type": "string", "description": "Guild ID (optional)"}
            }
        }
    },
    handler=lambda args, **kw: get_guild_info(args.get("guild_id")),
    check_fn=check_requirements
)