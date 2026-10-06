import logging
import os
import threading
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from pydantic import BaseModel
from strands import Agent
from strands.models.openai import OpenAIModel
from amp_instrumentation import init_otel

log = logging.getLogger("strands-chatbot")

# 0. Config comes from env vars AMP injects at runtime (no .env on AMP)
# Export Strands' native OTel GenAI spans to AMP (must run before Agent is created)
init_otel()

# 1. INFO logs land in the AMP agent logs view
logging.basicConfig(level=logging.INFO)

# 2. Define the Agent's personality and tools
# (To use a cloud model, omit the 'model' parameter to default to Bedrock, 
# or pass a string like model="openai/gpt-4o")

#define model
# AMP injects the LLM gateway URL + platform-issued key for the agent's LLM configuration.
# Names default to {TEMPLATE}_URL / {TEMPLATE}_API_KEY (OPENAI_* here) and can be renamed in the AMP console.
LLM_GATEWAY_URL = os.getenv("OPENAI_URL")
LLM_GATEWAY_KEY = os.getenv("OPENAI_API_KEY")
if not (LLM_GATEWAY_URL and LLM_GATEWAY_KEY):
    # Fail fast - no silent fallback to an ungoverned endpoint
    raise RuntimeError("OPENAI_URL / OPENAI_API_KEY not set - attach an LLM configuration to this agent in AMP")

# Model knobs come from env so swapping LLM providers in AMP is a redeploy, not a rebuild
MODEL = os.getenv("MODEL", "gpt-4o-mini") # use env variable and if missing default the model
params: dict[str, Any] = {}
if os.getenv("TEMPERATURE"):
    params["temperature"] = float(os.environ["TEMPERATURE"])
if os.getenv("REASONING_EFFORT"):
    # Ollama thinking models (e.g. qwen3.5) can out-think the gateway's 30s upstream timeout - set "none" there.
    # Most OpenAI models reject this param, so leave it unset for them.
    params["reasoning_effort"] = os.environ["REASONING_EFFORT"]
log.info("LLM gateway=%s model=%s params=%s", LLM_GATEWAY_URL, MODEL, params)

model = OpenAIModel(
    client_args={
        "base_url": LLM_GATEWAY_URL,
        # Gateway auths on the API-Key header. openai>=3 rejects an empty api_key,
        # so pass the key here and blank the Bearer header it would otherwise send
        "api_key": LLM_GATEWAY_KEY,
        "default_headers": {"API-Key": LLM_GATEWAY_KEY, "Authorization": ""},
    },
    model_id=MODEL,
    params=params,
    # Gateway holds streamed responses open past [DONE] until a ~30s idle timeout,
    # which the SDK reports as a broken stream. The /chat contract returns one JSON blob anyway.
    stream=False,
)

# Small model (qwen3:4b): short, plain, direct instructions work best
SYSTEM_PROMPT = (
    "You are a friendly, helpful chat assistant. "
    "Answer clearly and briefly. "
    "If you don't know something, say so instead of guessing. "
    "Ask a short follow-up question if the request is unclear."
)

# 3. One Agent per session_id - each Strands Agent keeps its own conversation history.
# In-memory only: history resets on restart and isn't shared across replicas.
_sessions: dict[str, tuple[Agent, threading.Lock]] = {}
_sessions_lock = threading.Lock()


def _get_session(session_id: str) -> tuple[Agent, threading.Lock]:
    with _sessions_lock:
        if session_id not in _sessions:
            agent = Agent(
                system_prompt=SYSTEM_PROMPT,
                model=model,  # Routed through the AMP LLM gateway
                callback_handler=None,  # Reply goes back in the HTTP response, not stdout
            )
            _sessions[session_id] = (agent, threading.Lock())
        return _sessions[session_id]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    # 5. Flush buffered spans before the process exits
    trace.get_tracer_provider().force_flush()


# 4. AMP chat-api contract: POST /chat on port 8000, {message, session_id, context?} -> {response}
app = FastAPI(title="Strands Chatbot", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    session_id: str
    context: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    response: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")
    agent, lock = _get_session(req.session_id)
    try:
        # Strands Agents aren't safe for concurrent calls - serialize turns within a session
        with lock:
            result = agent(req.message)
    except Exception as exc:
        log.exception("agent run failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ChatResponse(response=str(result).strip())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
