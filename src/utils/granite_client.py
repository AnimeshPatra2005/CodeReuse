# Backwards compatibility shim — import from llm_client instead
from src.utils.llm_client import LLMClient as GraniteClient  # noqa: F401

__all__ = ["GraniteClient"]