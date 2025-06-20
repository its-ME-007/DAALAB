from google.adk.agents import LlmAgent,Agent
# from google.adk.sessions import InMemorySession
from .tools.tools import read_code
import os

root_agent = Agent(
    name = "Codey",
    description = "A helpful assistant that can read code and help with tasks.",
    instruction = """You are a helpful assistant that can read code and help with tasks. The user's code is in the code.py file.
    Help the user with their code by reading it and understanding the code using the read_code tool automatically at the start of the session.
    Greet the user with a friendly message and ask them what they would like to do. Do not ask them to read the code again. Ask the user if their code is in code.py file.
    If the user says yes continue with conversation. If the user says no, ask them to provide the code.""",
    model = "gemini-2.0-flash",
    tools = [read_code],
)
    