import json
import requests
from tools.registry import registry

REDDIT_API_URL = "https://www.reddit.com"
REDDIT_USER_AGENT = "Memetrader/1.0"


def check_requirements() -> bool:
    """Check if Reddit API is accessible (no auth needed for public)"""
    return True


def get_subreddit_posts(subreddit: str, limit: int = 10, sort: str = "hot") -> str:
    """Get posts from a subreddit"""
    try:
        url = f"{REDDIT_API_URL}/r/{subreddit}/{sort}.json"
        params = {"limit": min(limit, 100)}
        headers = {"User-Agent": REDDIT_USER_AGENT}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        posts = []
        for item in data.get("data", {}).get("children", []):
            post = item.get("data", {})
            posts.append({
                "id": post.get("id"),
                "title": post.get("title", "")[:100],
                "author": post.get("author"),
                "score": post.get("score"),
                "num_comments": post.get("num_comments"),
                "url": post.get("url", "")[:100],
                "created_utc": post.get("created_utc"),
                "subreddit": post.get("subreddit")
            })
        
        return json.dumps({"subreddit": subreddit, "posts": posts})
    except Exception as e:
        return json.dumps({"error": str(e)})


def search_subreddit(subreddit: str, query: str, limit: int = 10) -> str:
    """Search for posts in a subreddit"""
    try:
        url = f"{REDDIT_API_URL}/r/{subreddit}/search.json"
        params = {"q": query, "limit": min(limit, 100), "sort": "relevance"}
        headers = {"User-Agent": REDDIT_USER_AGENT}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("data", {}).get("children", []):
            post = item.get("data", {})
            results.append({
                "id": post.get("id"),
                "title": post.get("title", "")[:100],
                "author": post.get("author"),
                "score": post.get("score"),
                "num_comments": post.get("num_comments"),
                "url": post.get("url", "")[:100]
            })
        
        return json.dumps({
            "subreddit": subreddit,
            "query": query,
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_post_comments(post_id: str) -> str:
    """Get comments for a Reddit post"""
    try:
        url = f"{REDDIT_API_URL}/comments/{post_id}.json"
        headers = {"User-Agent": REDDIT_USER_AGENT}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        comments = []
        if len(data) > 1:
            for item in data[1].get("data", {}).get("children", []):
                comment = item.get("data", {})
                comments.append({
                    "id": comment.get("id"),
                    "author": comment.get("author"),
                    "body": comment.get("body", "")[:200],
                    "score": comment.get("score"),
                    "created_utc": comment.get("created_utc")
                })
        
        return json.dumps({"post_id": post_id, "comments": comments})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_trending_subreddits() -> str:
    """Get trending subreddits"""
    try:
        url = f"{REDDIT_API_URL}/subreddits/trending.json"
        headers = {"User-Agent": REDDIT_USER_AGENT}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        subreddits = []
        for item in data.get("data", {}).get("children", []):
            sub = item.get("data", {})
            subreddits.append({
                "name": sub.get("display_name"),
                "title": sub.get("title", "")[:50],
                "subscribers": sub.get("subscribers"),
                "over_18": sub.get("over_18", False)
            })
        
        return json.dumps({"trending": subreddits})
    except Exception as e:
        return json.dumps({"error": str(e)})


registry.register(
    name="reddit_subreddit_posts",
    toolset="social",
    schema={
        "name": "reddit_subreddit_posts",
        "description": "Get posts from a subreddit",
        "parameters": {
            "type": "object",
            "properties": {
                "subreddit": {"type": "string", "description": "Subreddit name (without r/)"},
                "limit": {"type": "integer", "description": "Max posts", "default": 10},
                "sort": {"type": "string", "description": "Sort by (hot/new/top)", "default": "hot"}
            },
            "required": ["subreddit"]
        }
    },
    handler=lambda args, **kw: get_subreddit_posts(
        args.get("subreddit", ""),
        args.get("limit", 10),
        args.get("sort", "hot")
    ),
    check_fn=check_requirements
)

registry.register(
    name="reddit_search",
    toolset="social",
    schema={
        "name": "reddit_search",
        "description": "Search posts in a subreddit",
        "parameters": {
            "type": "object",
            "properties": {
                "subreddit": {"type": "string", "description": "Subreddit name"},
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["subreddit", "query"]
        }
    },
    handler=lambda args, **kw: search_subreddit(
        args.get("subreddit", ""),
        args.get("query", ""),
        args.get("limit", 10)
    ),
    check_fn=check_requirements
)

registry.register(
    name="reddit_post_comments",
    toolset="social",
    schema={
        "name": "reddit_post_comments",
        "description": "Get comments for a Reddit post",
        "parameters": {
            "type": "object",
            "properties": {
                "post_id": {"type": "string", "description": "Reddit post ID"}
            },
            "required": ["post_id"]
        }
    },
    handler=lambda args, **kw: get_post_comments(args.get("post_id", "")),
    check_fn=check_requirements
)

registry.register(
    name="reddit_trending",
    toolset="social",
    schema={
        "name": "reddit_trending",
        "description": "Get trending subreddits",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    handler=lambda args, **kw: get_trending_subreddits(),
    check_fn=check_requirements
)