"""Guided, presenter-controlled demo of the PACT protocol.

The orchestrator turns the Tokyo-travel scenario into discrete, clickable steps.
Each step is driven by Mercury 2 (the LLM decides which tools to call) and returns
a structured trace so the dashboard can show what the AI thinks and how agents
talk to each other. A deterministic fallback keeps the demo alive without an API key.
"""
