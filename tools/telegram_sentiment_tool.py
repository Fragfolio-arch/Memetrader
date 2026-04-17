import json
import os
import requests
from tools.registry import registry

TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL", "https://api.telegram.org")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def check_requirements() -> bool:
    """Check if Telegram API is accessible (requires bot token)"""
    return bool(TELEGRAM_BOT_TOKEN)


def get_channel_messages(channel_username: str, limit: int = 10) -> str:
    """Get recent messages from a Telegram channel"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            return json.dumps({"error": "TELEGRAM_BOT_TOKEN not configured"})
        
        chat_id = channel_username
        if not channel_username.startswith("@"):
            chat_id = f"@{channel_username}"
        
        url = f"{TELEGRAM_API_URL}/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        messages = []
        if data.get("ok"):
            for msg in data.get("result", [])[:limit]:
                msg_data = msg.get("message", {})
                if msg_data.get("chat", {}).get("username") == channel_username.replace("@", ""):
                    messages.append({
                        "message_id": msg_data.get("message_id"),
                        "text": msg_data.get("text", "")[:200],
                        "date": msg_data.get("date"),
                        "from": msg_data.get("from", {}).get("first_name", "Unknown")
                    })
        
        return json.dumps({"channel": channel_username, "messages": messages})
    except Exception as e:
        return json.dumps({"error": str(e)})


def search_channel(channel_username: str, query: str, limit: int = 10) -> str:
    """Search for messages in a Telegram channel"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            return json.dumps({"error": "TELEGRAM_BOT_TOKEN not configured"})
        
        url = f"{TELEGRAM_API_URL}/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        if data.get("ok"):
            for msg in data.get("result", []):
                msg_data = msg.get("message", {})
                text = msg_data.get("text", "") or msg_data.get("caption", "")
                if query.lower() in text.lower():
                    results.append({
                        "message_id": msg_data.get("message_id"),
                        "text": text[:200],
                        "date": msg_data.get("date")
                    })
                    if len(results) >= limit:
                        break
        
        return json.dumps({
            "channel": channel_username,
            "query": query,
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_channel_info(channel_username: str) -> str:
    """Get channel information"""
    try:
        if not TELEGRAM_BOT_TOKEN:
            return json.dumps({"error": "TELEGRAM_BOT_TOKEN not configured"})
        
        chat_id = channel_username
        if not channel_username.startswith("@"):
            chat_id = f"@{channel_username}"
        
        url = f"{TELEGRAM_API_URL}/bot{TELEGRAM_BOT_TOKEN}/getChat"
        params = {"chat_id": chat_id}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("ok"):
            chat = data.get("result", {})
            return json.dumps({
                "title": chat.get("title"),
                "username": chat.get("username"),
                "type": chat.get("type"),
                "member_count": chat.get("member_count"),
                "description": chat.get("description", "")[:100]
            })
        return json.dumps({"error": "Channel not found"})
    except Exception as e:
        return json.dumps({"error": str(e)})


registry.register(
    name="telegram_channel_messages",
    toolset="social",
    schema={
        "name": "telegram_channel_messages",
        "description": "Get recent messages from a Telegram channel",
        "parameters": {
            "type": "object",
            "properties": {
                "channel_username": {"type": "string", "description": "Channel username (without @)"},
                "limit": {"type": "integer", "description": "Max messages", "default": 10}
            },
            "required": ["channel_username"]
        }
    },
    handler=lambda args, **kw: get_channel_messages(
        args.get("channel_username", ""),
        args.get("limit", 10)
    ),
    check_fn=check_requirements
)

registry.register(
    name="telegram_search",
    toolset="social",
    schema={
        "name": "telegram_search",
        "description": "Search messages in a Telegram channel",
        "parameters": {
            "type": "object",
            "properties": {
                "channel_username": {"type": "string", "description": "Channel username"},
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["channel_username", "query"]
        }
    },
    handler=lambda args, **kw: search_channel(
        args.get("channel_username", ""),
        args.get("query", ""),
        args.get("limit", 10)
    ),
    check_fn=check_requirements
)

registry.register(
    name="telegram_channel_info",
    toolset="social",
    schema={
        "name": "telegram_channel_info",
        "description": "Get information about a Telegram channel",
        "parameters": {
            "type": "object",
            "properties": {
                "channel_username": {"type": "string", "description": "Channel username"}
            },
            "required": ["channel_username"]
        }
    },
    handler=lambda args, **kw: get_channel_info(args.get("channel_username", "")),
    check_fn=check_requirements
)