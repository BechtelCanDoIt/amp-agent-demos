# Strands Chatbot - External Agent with AMP Tracing

A small AWS Strands chat agent that runs on your laptop against a local Ollama model and ships its traces to WSO2 Agent Manager (AMP). AMP doesn't host this one. It just watches. That's the "external agent" pattern: your code runs wherever it runs, and AMP still gets full observability.

## How it fits together

```
you (terminal) --> chatagent.py (Strands Agent, one conversation)
                         |                    |
                         v                    v
              Ollama (localhost:11434)   AMP OTel endpoint (traces)
```

`chatagent.py` is a plain terminal chat loop. One Strands Agent lives for the whole session, so it remembers what you said earlier in the conversation. Type `exit` or `quit` (or hit Ctrl+C) to leave.

`init_otel()` from `amp-instrumentation` runs before the agent gets created, so every turn shows up in the AMP Traces view with the Strands and Ollama spans nested underneath. On the way out the script force-flushes the tracer so the last turn doesn't get lost in a buffer.

## Prerequisites

- Python 3.11
- [Ollama](https://ollama.com/) running locally on port `11434`, with your model pulled (`ollama pull qwen3:4b`)
- An AMP instance you can reach, with an **external agent** registered so you have an agent API key

## Environment variables

Create a `.env` in this folder (it's gitignored):

```
# Local Ollama model
MODEL=qwen3:4b

## WSO2 Agent Manager ###########################################################

export AMP_OTEL_ENDPOINT="http://localhost:19080/otel"

## WARNING: this should be in a vault - putting here for development/demo purposes
export AMP_AGENT_API_KEY="" # GET from locally running Agent Manager

## Strands: put prompt/response content on span attributes (AMP does not read span events)
export OTEL_SEMCONV_STABILITY_OPT_IN="gen_ai_latest_experimental,gen_ai_span_attributes_only"

## END WSO2 Agent Manager ######################################################
```

| Variable | Default | Notes |
|---|---|---|
| `MODEL` | `qwen2.5:14b-instruct` | Any model you've pulled into Ollama |
| `AMP_OTEL_ENDPOINT` | none | Where AMP collects traces. The example points at a local AMP |
| `AMP_AGENT_API_KEY` | none | From the external agent you registered in AMP |
| `OTEL_SEMCONV_STABILITY_OPT_IN` | none | **Set this or your traces show up with no prompt or response text.** AMP reads span attributes, not span events |

## To run agent

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
source .env && python3 chatagent.py
```

Ask it something, then go check the Traces view in AMP for that agent.

## 💡 Tips

- The system prompt is short and plain on purpose. Small models like qwen3:4b follow simple, direct instructions much better than long clever ones.
- The model runs at temperature 0, so you get the same answer to the same question. Handy for demos.
- Want to see the agent's internals in the terminal? Uncomment the `logging.basicConfig(level=logging.INFO)` line.

## 📚 Docs

- [Strands Agents: Ollama model provider](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/ollama/)
- [AMP manual-instrumentation sample](https://github.com/wso2/agent-manager/tree/main/samples/manual-instrumentation-agent)

Anything missing or wrong is my fault - open an issue and I'll fix it right up!
