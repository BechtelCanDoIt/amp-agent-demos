# amp-agent-demos

Small, runnable agent demos for WSO2 Agent Manager (AMP). Each folder stands on its own with its own `requirements.txt`, `.env`, and README.

## AWS Strands: External Chat Agent

[`aws-strands/external-chat-agent`](aws-strands/external-chat-agent/README.md)

A terminal chat agent that runs on your laptop against local Ollama and sends its traces to AMP. Shows the external agent pattern: AMP observes, you host.

## AWS Strands: Tool Calling Example

[`aws-strands/tool-example`](aws-strands/tool-example/README.md)

A one-shot Strands agent with the pre-built `calculator` and `current_time` tools. Runs locally on Ollama and traces to AMP, so you can watch the tool calls as spans.

## AWS Strands: Hosted in AMP

[`aws-strands/hosted-internally`](aws-strands/hosted-internally/README.md)

A FastAPI chat agent that AMP builds, hosts, and routes through the AMP LLM gateway. Follows the AMP chat agent contract (`POST /chat`).
