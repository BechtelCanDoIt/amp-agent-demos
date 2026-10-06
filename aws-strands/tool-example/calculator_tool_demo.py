import logging
import os
from strands import Agent
from strands.models.ollama import OllamaModel
from strands_tools import calculator, current_time  # Pre-built tools
from dotenv import load_dotenv
from amp_instrumentation import init_otel

# 0. Load in dotenv
load_dotenv()

# 0b. Export Strands' native OTel GenAI spans to AMP (must run before Agent is created)
init_otel()

# 1. Turn on debugging to see how the agent reasons in the terminal
logging.basicConfig(level=logging.INFO)

# 2. Define the Agent's personality and tools
# (To use a cloud model, omit the 'model' parameter to default to Bedrock, 
# or pass a string like model="openai/gpt-4o")

#define model
MODEL = os.getenv("MODEL", "qwen2.5:14b-instruct")
model = OllamaModel(host="http://localhost:11434", model_id=MODEL, temperature=0)

my_agent = Agent(
    system_prompt="You are a precise, helpful personal assistant. Use tools whenever calculations are needed.",
    model=model,  # Pointing to your local Ollama instance
    tools=[calculator, current_time]
)

# 3. Invoke the agent like a function
prompt = "What is 1+1"
print(f"User: {prompt}\n")

response = my_agent(prompt)
print(f"\nAgent Response:\n{response}")

# 4. Flush buffered spans before the short-lived script exits
from opentelemetry import trace
trace.get_tracer_provider().force_flush()
