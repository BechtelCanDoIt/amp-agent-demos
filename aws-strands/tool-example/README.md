# TODO

## Required
Create .env file with:

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

## To run agent
`source .env && python3 calculator_tool_demo.py`
