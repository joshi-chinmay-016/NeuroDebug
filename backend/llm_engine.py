"""
Deprecated module: NeuroDebug LLM engine.
Please import from `llm.client` and `llm.prompt_builder` instead.
"""

from llm.client import GroqClient
from llm.prompt_builder import PromptBuilder

__all__ = ["GroqClient", "PromptBuilder"]
