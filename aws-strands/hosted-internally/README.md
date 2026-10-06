# Strands Chatbot - Hosted in WSO2 Agent Manager

A small AWS Strands chat agent that runs inside WSO2 Agent Manager (AMP) and talks to its model through the AMP LLM gateway. AMP builds it straight from this folder, hosts it, injects the LLM credentials, and collects the traces. The agent code never sees a raw provider key... and that's the whole point.

## How it fits together

```
caller --> AMP agent endpoint --> POST /chat (this app, port 8000)
                                       |
                                       v
                          Strands Agent (one per session_id)
                                       |
                                       v
                     AMP LLM gateway (API-Key header) --> OpenAI / Ollama / ...
```

`amp-feature-demo.py` is a FastAPI app that follows the AMP chat agent contract:

| | |
|---|---|
| Endpoint | `POST /chat` on `0.0.0.0:8000` |
| Request | `{"message": "...", "session_id": "...", "context": {}}` (`context` is optional) |
| Response | `{"response": "..."}` |
| Health | `GET /health` returns `{"status": "ok"}` |

Each `session_id` gets its own Strands Agent, so conversation history carries across turns. History lives in memory, which means a restart wipes it and two replicas won't share it. Fine for a demo. You'd want a real session store before going further.

Traces go to AMP through `amp-instrumentation` (`init_otel()` runs before any agent gets created), so every `/chat` call shows up in the AMP Traces view with the FastAPI, Strands and LLM spans nested underneath.

## Environment variables

AMP injects the first two when you attach an LLM provider to the agent. The rest you set yourself in the agent's environment in AMP. **Changing any of these is a redeploy, not a rebuild.**

| Variable | Set by | Default | Notes |
|---|---|---|---|
| `OPENAI_URL` | AMP (LLM config) | none - required | Gateway base URL for the provider |
| `OPENAI_API_KEY` | AMP (LLM config) | none - required | Platform-issued gateway key, sent as the `API-Key` header |
| `MODEL` | you | `gpt-4o-mini` | Must exist on whatever the provider points at |
| `TEMPERATURE` | you | not sent | Leave unset for gpt-5 family models (they reject it) |
| `REASONING_EFFORT` | you | not sent | Set `none` for Ollama thinking models like qwen3.5. Leave unset for most OpenAI models (they reject it) |

If `OPENAI_URL` or `OPENAI_API_KEY` is missing, the app refuses to start and tells you to attach an LLM configuration. That's on purpose - no quiet fallback to some unmanaged endpoint.

The variable names come from the provider template (`{TEMPLATE}_URL` / `{TEMPLATE}_API_KEY`). The AMP console lets you rename them, so if you do, rename them in the code too.

Quick settings for the two providers I've run this against:

| Provider | `MODEL` | `TEMPERATURE` | `REASONING_EFFORT` |
|---|---|---|---|
| OpenAI | unset (or e.g. `gpt-4.1-mini`) | optional | unset |
| Ollama on prod.aten | `qwen3.5:latest` | `0` | `none` |

## Deploying in AMP

1. Create the agent as a **Chat Agent** (the `chat-api` type). That type pins the port to 8000 and the path to `/chat`.
2. Point the source at this repo, branch `main`, folder `aws-strands/hosted-internally`, Python 3.11. Start command is `python amp-feature-demo.py`.
3. Attach **one** LLM provider to the agent and confirm the provider's Overview says it's deployed to a gateway.
4. Set `MODEL` (and friends) in the agent's environment if the defaults don't fit.
5. Build, deploy, then send `ping` from **Try It**. You should get a pong back and a green trace with token counts.

## 🐞 Gotchas we hit getting here

These all cost real time, so here they are in one spot.

**Two providers, one set of variables.** Attach two providers built on the same template and both inject `OPENAI_URL` / `OPENAI_API_KEY`. Which one wins is anyone's guess. Keep exactly one attached. The startup log prints `LLM gateway=... model=... params=...` (never the key), so check that first when something looks off.

**Saved isn't deployed.** Editing a provider (say, the Upstream URL) saves a new revision, but the gateways keep serving the old one until you deploy it. The Deployment tab can still say "Deployed" for the old revision while Overview says "Not deployed". Trust Overview.

**The missing `/v1`.** Ollama's OpenAI-compatible API lives under `/v1`. If the provider's Upstream URL is `http://host:11434` instead of `http://host:11434/v1`, every call 404s with `{"error":"Not Found"}` and the model never even loads.

**The Hanging Stream.** With streaming on, the gateway sends the full answer and `[DONE]`, then holds the connection open until a ~30 second idle timeout and drops it. The OpenAI SDK reads that as a broken response. The app runs with `stream=False`, which costs nothing since `/chat` returns one JSON blob anyway.

**The Overthinker.** qwen3.5 reasons before it answers. Ask it something open-ended at temperature 0 and it can think right past the gateway's 30 second upstream timeout and come back as a 504. `REASONING_EFFORT=none` takes those calls from 30+ seconds to under one.

**Empty `api_key`.** The AMP console snippet passes `api_key=""` to the OpenAI client. openai 3.x rejects that outright. The app passes the gateway key as `api_key` and blanks the `Authorization` header, so auth still rides on `API-Key`.

## 📚 Docs

- [AMP: Configure Agent LLM Configuration](https://wso2.github.io/docs-agent-platform/next/guides/configure-agent-llm-configuration/)
- [AMP: LLM Service Provider](https://wso2.github.io/docs-agent-platform/next/concepts/llm-service-provider/)
- [AMP chat agent OpenAPI schema](https://github.com/wso2/agent-manager/blob/main/agent-manager-service/clients/openchoreosvc/client/default-openapi-schema.yaml)
- [AMP manual-instrumentation sample](https://github.com/wso2/agent-manager/tree/main/samples/manual-instrumentation-agent)
- [Strands Agents: `OpenAIModel` source](https://github.com/strands-agents/harness-sdk/blob/main/strands-py/src/strands/models/openai.py)

Anything missing or wrong is my fault - open an issue and I'll fix it right up!
