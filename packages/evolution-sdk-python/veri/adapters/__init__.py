"""
VERI Framework Adapters Package
Provides automated integration and tracing for agent frameworks:
- CrewAI
- AutoGen
- LlamaIndex
"""

from veri.adapters.crewai import patch_crewai
from veri.adapters.autogen import patch_autogen
from veri.adapters.llamaindex import patch_llamaindex

__all__ = ["patch_crewai", "patch_autogen", "patch_llamaindex"]
