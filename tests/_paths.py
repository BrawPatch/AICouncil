"""Makes the MultiAgentCouncil modules importable from tests.

The council modules use flat imports (`from llm_client import ...`, `from agents.coder import ...`)
because they are launched from inside MultiAgentCouncil/. Import this module first in any test:

    import _paths  # noqa: F401
"""
import sys
from pathlib import Path

COUNCIL_DIR = Path(__file__).resolve().parent.parent / "MultiAgentCouncil"

if str(COUNCIL_DIR) not in sys.path:
    sys.path.insert(0, str(COUNCIL_DIR))
