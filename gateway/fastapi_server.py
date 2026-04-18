"""
FastAPI Server for Workspace UI Backend

Handles:
- Session management (SQLite)
- Chat completions (LLM calls)
- Tools execution
- Trading (all endpoints)

Port: 8643

External dependencies: LLM APIs (Anthropic, OpenAI), CoinGecko (via price_oracle)
"""

import logging
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import Depends
import time
from collections import defaultdict

from hermes_cli.config import load_config
from hermes_state import SessionDB
from tools.memory_tool import MemoryStore
from tools.skills_tool import skill_view, skills_categories, skills_list
from tools.crypto.price_oracle import (
    get_token_price,
    get_trending_meme_tokens,
    get_prices_batch,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Rate Limiting Middleware
# ============================================================================

class RateLimitMiddleware:
    """Simple in-memory rate limiter per IP address."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)

    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old requests (older than 1 minute)
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if current_time - t < 60
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        response = await call_next(request)
        return response


# ============================================================================
# FastAPI App & Lifecycle
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("[FastAPI] Starting Workspace UI Backend on port 8643")

    # Initialize session DB
    app.state.session_db = SessionDB()
    app.state.memory_store = MemoryStore()

    logger.info("[FastAPI] Session DB and Memory Store initialized")

    # Start Cron scheduler in background thread
    import threading
    import time
    import cron.scheduler

    def run_cron_tick():
        """Run cron tick every 60 seconds"""
        while True:
            try:
                cron.scheduler.tick()
            except Exception as e:
                logger.error(f"[Cron] Error in tick: {e}")
            time.sleep(60)

    cron_thread = threading.Thread(
        target=run_cron_tick, daemon=True, name="cron-scheduler"
    )
    cron_thread.start()
    logger.info("[FastAPI] Cron scheduler started")

    yield

    logger.info("[FastAPI] Shutting down")


app = FastAPI(
    title="Hermes Workspace API",
    description="Backend API for Workspace UI - sessions, chat, trading",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting - 60 requests per minute per IP
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)


# ============================================================================
# Authentication
# ============================================================================


def verify_api_key(authorization: Optional[str] = Header(None)) -> bool:
    """Verify Bearer token - returns True if valid or no key configured."""
    expected_key = os.getenv("HERMES_API_KEY")
    if not expected_key:
        return True  # No key configured - allow all

    if not authorization:
        return False  # No auth header

    if authorization.startswith("Bearer "):
        token = authorization[7:]
        return token == expected_key

    return False


async def require_auth(authorization: Optional[str] = Header(None)) -> None:
    """Dependency that requires valid auth - raises 401 if invalid."""
    if not verify_api_key(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ============================================================================
# Helpers
# ============================================================================


def get_session_db(request: Request) -> SessionDB:
    """Get session DB from app state."""
    return request.app.state.session_db


def get_current_model(config: Dict) -> Dict:
    """Get current model settings from config."""
    model_cfg = config.get("model", {})
    if isinstance(model_cfg, dict):
        return {
            "model": model_cfg.get("default", "anthropic/claude-sonnet-4-20250514"),
            "provider": model_cfg.get("provider", "anthropic"),
            "api_mode": model_cfg.get("api_mode", "chat_completions"),
            "base_url": model_cfg.get("base_url", ""),
        }
    return {
        "model": str(model_cfg) if model_cfg else "anthropic/claude-sonnet-4-20250514",
        "provider": "anthropic",
        "api_mode": "chat_completions",
        "base_url": "",
    }


# ============================================================================
# Health & Config
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "platform": "hermes-workspace", "backend": "fastapi"}


@app.get("/api/config")
async def get_config(request: Request):
    """Get current configuration."""
    config = load_config()
    current = get_current_model(config)
    return {
        "model": current["model"],
        "provider": current["provider"],
        "api_mode": current["api_mode"],
        "base_url": current["base_url"],
        "config": config,
    }


@app.patch("/api/config")
async def patch_config(request: Request):
    """Update configuration at runtime."""
    from hermes_cli.config import save_config

    body = await request.json()

    try:
        config = load_config()
        config.update(body)
        save_config(config)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/hermes-config")
async def get_hermes_config(request: Request):
    """Get full configuration - alias for /api/config for UI compatibility."""
    return await get_config(request)


@app.get("/api/available-models")
async def available_models(request: Request):
    """List available models."""
    from hermes_cli.models import curated_models_for_provider, list_available_providers

    config = load_config()
    current = get_current_model(config)
    provider = current["provider"] or "anthropic"

    models = [
        {"id": model_id, "description": description, "provider": provider}
        for model_id, description in curated_models_for_provider(provider)
    ]

    providers = list_available_providers()
    return {"provider": provider, "models": models, "providers": providers}


# ============================================================================
# Sessions API
# ============================================================================


@app.get("/api/sessions")
async def list_sessions(request: Request, limit: int = 50, offset: int = 0):
    """List all sessions."""
    db = get_session_db(request)
    sessions = db.list_sessions_rich(limit=limit, offset=offset)
    total = db.session_count()
    return {"items": sessions, "total": total}


@app.post("/api/sessions")
async def create_session(request: Request):
    """Create a new session."""
    import uuid

    db = get_session_db(request)
    try:
        body = await request.json()
    except Exception:
        body = {}

    title = body.get("title", "New Session")
    session_id = str(uuid.uuid4())
    db.create_session(
        session_id=session_id, source="fastapi", model="opencode/big-pickle"
    )

    return {
        "session": db.get_session(session_id),
        "session_id": session_id,
    }


@app.get("/api/sessions/{session_id}")
async def get_session(request: Request, session_id: str):
    """Get a specific session."""
    db = get_session_db(request)
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": session}


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(request: Request, session_id: str, limit: int = 100):
    """Get messages for a session."""
    db = get_session_db(request)
    messages = db.get_messages(session_id) or []
    # Apply limit
    return {
        "messages": messages[-limit:] if len(messages) > limit else messages,
        "session_id": session_id,
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(request: Request, session_id: str):
    """Delete a session."""
    db = get_session_db(request)
    db.delete_session(session_id)
    return {"ok": True}


@app.patch("/api/sessions/{session_id}")
async def update_session(request: Request, session_id: str):
    """Update session - title, system_prompt."""
    db = get_session_db(request)
    body = await request.json()

    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    title = body.get("title")
    if title is not None:
        db.set_session_title(session_id, title)

    system_prompt = body.get("system_prompt")
    if system_prompt is not None:
        db.update_system_prompt(session_id, system_prompt)

    return {"ok": True}


@app.post("/api/sessions/{session_id}/fork")
async def fork_session(request: Request, session_id: str):
    """Fork a session with its messages."""
    db = get_session_db(request)

    original = db.get_session(session_id)
    if not original:
        raise HTTPException(status_code=404, detail="Session not found")

    forked_id = f"sess_{uuid.uuid4().hex}"

    try:
        db.create_session(
            session_id=forked_id,
            source=original.get("source") or "fastapi",
            model=original.get("model"),
            system_prompt=original.get("system_prompt"),
            parent_session_id=session_id,
        )

        # Copy messages
        messages = db.get_messages(session_id)
        for msg in messages:
            db.append_message(
                session_id=forked_id,
                role=msg.get("role"),
                content=msg.get("content"),
                tool_name=msg.get("tool_name"),
                tool_calls=msg.get("tool_calls"),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    forked = db.get_session(forked_id)
    return {"session": forked, "forked_from": session_id}


@app.get("/api/sessions/search")
async def search_sessions(request: Request, q: str = ""):
    """Search messages across all sessions."""
    if not q:
        raise HTTPException(status_code=400, detail="Missing query parameter: q")

    db = get_session_db(request)
    limit = int(request.query.get("limit", 20))
    results = db.search_messages(query=q, limit=limit)

    return {"query": q, "count": len(results), "results": results}


# ============================================================================
# Chat Completions (simplified - delegates to existing logic)
# ============================================================================


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible chat completions using AIAgent.
    Full implementation mirroring Gateway's approach.
    """
    from run_agent import AIAgent
    import asyncio

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    messages = body.get("messages", [])
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    model = body.get("model", "opencode/big-pickle")
    stream = body.get("stream", False)
    last_message = messages[-1].get("content", "") if messages else ""
    conversation_history = messages[:-1]  # Conversation history

    try:
        # Normalize model ID - strip provider prefix (opencode/ ->)
        if model and "/" in model:
            model = model.split("/", 1)[1]

        # Resolve runtime provider (model, api_key, etc.)
        from hermes_cli.runtime_provider import resolve_runtime_provider
        from hermes_cli.auth import PROVIDER_REGISTRY

        # Get config and resolve provider
        config = load_config()
        model_cfg = config.get("model", {})
        provider_name = model_cfg.get("provider", "opencode-zen")

        # Get provider settings from config
        custom_providers = config.get("custom_providers", [])
        provider_settings = None
        for p in custom_providers:
            if p.get("name") == provider_name:
                provider_settings = p
                break

        if provider_settings:
            api_key = provider_settings.get("api_key", "")
            base_url = provider_settings.get("base_url", "")
            api_mode = provider_settings.get("api_mode", "chat_completions")
        else:
            # Default to OpenCode Zen
            api_key = os.getenv("OPENCODE_ZEN_API_KEY", "")
            base_url = "https://opencode.ai/zen/v1/chat/completions"
            api_mode = "chat_completions"

        # Create AIAgent with resolved settings
        agent = AIAgent(
            model=model,
            api_key=api_key,
            base_url=base_url,
            provider=provider_name,
            api_mode=api_mode,
            max_iterations=90,
            quiet_mode=True,
            platform="fastapi",
        )

        # Run conversation in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: agent.run_conversation(
                last_message, conversation_history=conversation_history
            ),
        )

        final_response = result.get("final_response", "No response")

        import time

        return JSONResponse(
            content={
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": final_response,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }
        )

    except Exception as e:
        logger.error(f"[Chat] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# ============================================================================
# Skills API
# ============================================================================


@app.get("/api/skills")
async def list_skills(request: Request):
    """List all available skills."""
    import json

    skills_result = skills_list()
    try:
        skills_data = json.loads(skills_result)
        return skills_data
    except:
        return {"skills": skills_result}


@app.get("/api/skills/categories")
async def skills_category_list(request: Request):
    """List skill categories."""
    categories = skills_categories()
    return {"categories": categories}


@app.get("/api/skills/{name}")
async def view_skill(request: Request, name: str):
    """Get a specific skill."""
    skill = skill_view(name)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"skill": skill}


@app.post("/api/skills/{name}/install")
async def install_skill(request: Request, name: str):
    """Install a skill to project."""
    from pathlib import Path
    from hermes_constants import get_hermes_home
    import shutil

    global_skills_dir = Path(get_hermes_home()).parent / "skills"
    project_skills_dir = get_hermes_home() / "skills"

    source = global_skills_dir / name
    dest = project_skills_dir / name

    if not source.exists():
        raise HTTPException(status_code=404, detail="Skill not found in global skills")

    try:
        shutil.copytree(source, dest, dirs_exist_ok=True)
        return {"ok": True, "skill": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/skills/{name}/uninstall")
async def uninstall_skill(request: Request, name: str):
    """Uninstall a skill from project."""
    from pathlib import Path
    from hermes_constants import get_hermes_home
    import shutil

    project_skills_dir = get_hermes_home() / "skills"
    dest = project_skills_dir / name

    if not dest.exists():
        raise HTTPException(status_code=404, detail="Skill not found in project")

    try:
        shutil.rmtree(dest)
        return {"ok": True, "skill": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/skills/{name}/toggle")
async def toggle_skill(request: Request, name: str, enabled: bool = True):
    """Enable or disable a skill."""
    from pathlib import Path
    from hermes_constants import get_hermes_home

    project_skills_dir = get_hermes_home() / "skills"
    skill_dir = project_skills_dir / name

    if not skill_dir.exists():
        raise HTTPException(status_code=404, detail="Skill not found")

    # Create or update .disabled file
    disabled_file = skill_dir / ".disabled"
    try:
        if enabled:
            disabled_file.unlink(missing_ok=True)
        else:
            disabled_file.write_text("")
        return {"ok": True, "skill": name, "enabled": enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Memory API
# ============================================================================


@app.get("/api/memory")
async def get_memory(request: Request, query: str = ""):
    """Get memories."""
    store = request.app.state.memory_store
    if query:
        results = store.search(query)
    else:
        # Get formatted memory for system prompt
        user_memory = store.format_for_system_prompt("user") or ""
        self_memory = store.format_for_system_prompt("self") or ""
        results = {"user": user_memory, "self": self_memory}
    return {"memory": results}


@app.post("/api/memory")
async def add_memory(request: Request):
    """Add a memory."""
    store = request.app.state.memory_store
    try:
        body = await request.json()
        content = body.get("content", "")
        target = body.get("target", "user")
        if content:
            store.add(target, content)
            return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    raise HTTPException(status_code=400, detail="No content provided")


@app.patch("/api/memory")
async def replace_memory(request: Request):
    """Replace a memory entry."""
    store = request.app.state.memory_store
    body = await request.json()
    target = body.get("target", "user")
    old_text = body.get("old_text", "")
    new_text = body.get("new_text", "")

    if not old_text:
        raise HTTPException(status_code=400, detail="old_text required")

    try:
        store.replace(target, old_text, new_text)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/memory")
async def delete_memory(request: Request):
    """Delete a memory entry."""
    store = request.app.state.memory_store
    body = await request.json()
    target = body.get("target", "user")
    old_text = body.get("text", "")

    if not old_text:
        raise HTTPException(status_code=400, detail="text required")

    try:
        store.remove(target, old_text)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/trading/decision")
async def trading_decision(request: Request):
    """Get a trading decision from Hermes Agent."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    context = body.get("context", {})
    strategy = body.get("strategy", "meme_trading")
    exchange = body.get("exchange", "unknown")

    system_prompt = (
        "You are Hermes Agent, providing structured trading decisions for MemeTrader. "
        "Given the trading context, return only a valid JSON array of decision objects. "
        "Each decision must include at least `action` and `symbol`. Optional fields may include `confidence`, "
        "`leverage`, `stop_loss`, `take_profit`, `quantity`, `position_size_usd`, `price`, `order_id`, and `reasoning`. "
        "If no trade is recommended, return a single safe wait decision with action `wait` and symbol `ALL`. "
        "Do not include any markdown, explanation text, or additional wrapper objects outside the JSON array."
    )

    user_prompt = (
        f"Strategy: {strategy}\n"
        f"Exchange: {exchange}\n"
        "Trading Context:\n"
        f"{json.dumps(context, indent=2)}\n\n"
        "Return a valid JSON array of decisions."
    )

    try:
        config = load_config()
        current_model = get_current_model(config)
        provider_name = current_model["provider"]
        model = current_model["model"]
        api_mode = current_model["api_mode"]
        base_url = current_model["base_url"]

        custom_providers = config.get("custom_providers", [])
        provider_settings = next(
            (p for p in custom_providers if p.get("name") == provider_name),
            None,
        )

        if provider_settings:
            api_key = provider_settings.get("api_key", "")
            base_url = provider_settings.get("base_url", base_url)
            api_mode = provider_settings.get("api_mode", api_mode)
        else:
            api_key = os.getenv("OPENCODE_ZEN_API_KEY", "")
            if not base_url:
                base_url = "https://opencode.ai/zen/v1/chat/completions"
                api_mode = "chat_completions"

        from run_agent import AIAgent

        agent = AIAgent(
            model=model,
            api_key=api_key,
            base_url=base_url,
            provider=provider_name,
            api_mode=api_mode,
            max_iterations=10,
            quiet_mode=True,
            platform="fastapi",
        )

        loop = asyncio.get_event_loop()
        start_time = time.time()
        result = await loop.run_in_executor(
            None,
            lambda: agent.run_conversation(
                user_prompt,
                system_message=system_prompt,
                conversation_history=[],
            ),
        )
        duration_ms = int((time.time() - start_time) * 1000)
        raw_response = result.get("final_response", "") or ""

        decisions = []
        parsed = _extract_json_array(raw_response)
        if isinstance(parsed, list):
            decisions = parsed
        else:
            decisions = [
                {
                    "action": "wait",
                    "symbol": "ALL",
                    "reasoning": "Hermes did not return a valid decision array.",
                }
            ]

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "cot_trace": "",
            "raw_response": raw_response,
            "decisions": decisions,
            "ai_request_duration_ms": duration_ms,
        }
    except Exception as e:
        logger.error(f"[Trading Decision] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Trading decision failed: {str(e)}")


def _extract_json_array(raw: str):
    raw = raw.strip()
    if not raw:
        return None

    # Attempt to extract the first JSON array from the model output.
    array_match = re.search(r"(\[\s*\{.*?\}\s*\])", raw, re.S)
    if array_match:
        candidate = array_match.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Fallback: attempt to parse the whole response as JSON.
    try:
        return json.loads(raw)
    except Exception:
        return None


# ============================================================================
# Jobs API (Cron Jobs)
# ============================================================================


@app.get("/api/jobs")
async def list_jobs(request: Request):
    """List all cron jobs."""
    try:
        from cron.jobs import list_jobs as list_all_jobs

        jobs = list_all_jobs()
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs")
async def create_job(request: Request):
    """Create a new cron job."""
    try:
        from cron.jobs import create_job as cron_create_job

        body = await request.json()
        job = cron_create_job(
            prompt=body.get("prompt") or body.get("title", "Untitled Job"),
            schedule=body.get("schedule", "0 * * * *"),
            name=body.get("name") or body.get("title", "Untitled Job"),
            skill=body.get("skill"),
            skills=body.get("skills"),
            script=body.get("script"),
            model=body.get("model"),
            provider=body.get("provider"),
            base_url=body.get("base_url"),
            deliver=body.get("deliver", "local"),
        )
        return {"job": job}
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job_detail(request: Request, job_id: str):
    """Get a specific job."""
    try:
        from cron.jobs import get_job

        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job": job}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/jobs/{job_id}")
async def update_job(request: Request, job_id: str):
    """Update a job."""
    try:
        from cron.jobs import update_job as cron_update_job

        body = await request.json()
        job = cron_update_job(job_id, body)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job": job}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/jobs/{job_id}")
async def delete_job(request: Request, job_id: str):
    """Delete a job."""
    try:
        from cron.jobs import remove_job

        remove_job(job_id)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/{job_id}/pause")
async def pause_job(request: Request, job_id: str):
    """Pause a job."""
    try:
        from cron.jobs import pause_job as cron_pause_job

        job = cron_pause_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job": job}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/{job_id}/resume")
async def resume_job(request: Request, job_id: str):
    """Resume a paused job."""
    try:
        from cron.jobs import resume_job as cron_resume_job

        job = cron_resume_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job": job}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/{job_id}/resume")
async def resume_job(request: Request, job_id: str):
    """Resume a paused job."""
    try:
        from cron.jobs import resume_job as cron_resume_job

        job = cron_resume_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job": job}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/{job_id}/run")
async def trigger_job(request: Request, job_id: str):
    """Trigger immediate execution of a job."""
    try:
        from cron.jobs import trigger_job as cron_trigger_job

        job = cron_trigger_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"job": job, "status": "triggered"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}/output")
async def get_job_output(request: Request, job_id: str, limit: int = 10):
    """Get job output/history."""
    try:
        from cron.jobs import get_job
        from pathlib import Path
        from hermes_constants import get_hermes_home

        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        output_dir = get_hermes_home() / "cron" / "output" / job_id
        outputs = []

        if output_dir.exists():
            for f in sorted(
                output_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True
            )[:limit]:
                outputs.append(
                    {
                        "filename": f.name,
                        "content": f.read_text()[:5000],  # Limit content size
                        "timestamp": f.stat().st_mtime,
                    }
                )

        return {"job_id": job_id, "outputs": outputs}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job output: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hermes-jobs")
async def list_hermes_jobs(request: Request):
    """List all jobs - UI proxy endpoint."""
    return await list_jobs(request)


@app.get("/api/hermes-jobs/{job_id}")
async def get_hermes_job(request: Request, job_id: str):
    """Get a specific job - UI proxy endpoint."""
    return await get_job_detail(request, job_id)


@app.post("/api/hermes-jobs/{job_id}")
async def update_hermes_job(request: Request, job_id: str, action: str = None):
    """Update a job or perform action (pause/resume/run) - UI proxy endpoint."""
    if action == "pause":
        return await pause_job(request, job_id)
    elif action == "resume":
        return await resume_job(request, job_id)
    elif action == "run":
        return await trigger_job(request, job_id)
    else:
        return await update_job(request, job_id)


# ============================================================================
# Models API
# ============================================================================


@app.get("/v1/models")
async def list_models(request: Request):
    """List available models."""
    import time

    return {
        "object": "list",
        "data": [
            {
                "id": "hermes-agent",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "hermes",
                "permission": [],
                "root": "hermes-agent",
                "parent": None,
            }
        ],
    }


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Set HERMES_HOME if not set
    if not os.getenv("HERMES_HOME"):
        os.environ["HERMES_HOME"] = os.path.expanduser("~/.hermes")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8643,
        log_level="info",
    )
