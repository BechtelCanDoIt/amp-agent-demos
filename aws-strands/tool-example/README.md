# Strands Tool Calling - Calculator Demo with AMP Tracing

The smallest useful look at tool calling. A Strands agent gets two pre-built tools (`calculator` and `current_time` from `strands-agents-tools`), runs against a local Ollama model, and sends its traces to WSO2 Agent Manager (AMP). You get to see the model decide to call a tool, the tool run, and the answer come back... all as spans in AMP.

## How it fits together

```
calculator_tool_demo.py --> Strands Agent --> Ollama (localhost:11434)
                                 |
                                 +--> calculator / current_time tools
                                 |
                                 +--> AMP OTel endpoint (traces)
```

It's a one-shot script, not a chat loop. It sends a single hardcoded prompt (`What is 1+1`), prints the agent's response, flushes the traces, and exits. Change the `prompt` line in `calculator_tool_demo.py` to try something meatier.

INFO logging is on, so you'll see the agent's reasoning and tool calls stream by in the terminal.

## Prerequisites

- Python 3.11
- [Ollama](https://ollama.com/) running locally on port `11434`, with a model that supports tool calling pulled (`ollama pull qwen3:4b`)
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
| `MODEL` | `qwen2.5:14b-instruct` | Must support tool calling, or the agent will just guess at the math |
| `AMP_OTEL_ENDPOINT` | none | Where AMP collects traces. The example points at a local AMP |
| `AMP_AGENT_API_KEY` | none | From the external agent you registered in AMP |
| `OTEL_SEMCONV_STABILITY_OPT_IN` | none | **Set this or your traces show up with no prompt or response text.** AMP reads span attributes, not span events |

## To run agent

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
source .env && python3 calculator_tool_demo.py
```

Then open the trace in AMP. You should see the agent span, the model call, and a tool span for `calculator`.

## 💡 Tips

- The force-flush at the bottom of the script matters. Short-lived scripts can exit before the batch exporter sends anything, and then you're staring at an empty Traces view wondering what broke.
- Want more tools? `strands-agents-tools` ships a bunch of them. Import and add them to the `tools=[...]` list.

## 📚 Docs

- [Strands Agents: Tools overview](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/tools_overview/)
- [strands-agents-tools on GitHub](https://github.com/strands-agents/tools)
- [Strands Agents: Ollama model provider](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/ollama/)
- [AMP manual-instrumentation sample](https://github.com/wso2/agent-manager/tree/main/samples/manual-instrumentation-agent)

Anything missing or wrong is my fault - open an issue and I'll fix it right up!
