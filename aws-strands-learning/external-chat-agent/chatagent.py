import logging
import os
from strands import Agent
from strands.models.ollama import OllamaModel
from dotenv import load_dotenv
from amp_instrumentation import init_otel

# 0. Load in dotenv
load_dotenv()

# 0b. Export Strands' native OTel GenAI spans to AMP (must run before Agent is created)
init_otel()

# 1. Turn on debugging to see how the agent reasons in the terminal
#logging.basicConfig(level=logging.INFO)

# 2. Define the Agent's personality and tools
# (To use a cloud model, omit the 'model' parameter to default to Bedrock, 
# or pass a string like model="openai/gpt-4o")

#define model
MODEL = os.getenv("MODEL", "qwen2.5:14b-instruct") # use env variable and if missing default the model
model = OllamaModel(host="http://localhost:11434", model_id=MODEL, temperature=0)

# Small model (qwen3:4b): short, plain, direct instructions work best
SYSTEM_PROMPT = (
    "You are a friendly, helpful chat assistant. "
    "Answer clearly and briefly. "
    "If you don't know something, say so instead of guessing. "
    "Ask a short follow-up question if the request is unclear."
)

my_agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    model=model,  # Pointing to your local Ollama instance
    callback_handler=None,  # We print the reply ourselves below
)

# 3. Chat loop - the agent keeps conversation history between turns
print("Type 'exit' or 'quit' to leave.\n")
try:
    while True:
        try:
            user_input = input("How may I help you? ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        response = my_agent(user_input)
        print(f"\n{response}\n")
finally:
    # 4. Flush buffered spans before the script exits
    from opentelemetry import trace
    trace.get_tracer_provider().force_flush()
