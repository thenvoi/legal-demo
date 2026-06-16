"""Single switch for the platform Memory API (Enterprise-only).

The Memory API requires an Enterprise plan; on other plans every call returns
403 ``plan_required``.  Memory is therefore opt-in: it stays off unless
``BAND_ENABLE_MEMORY`` is set, so the demo runs on any account by default.

``load_dotenv()`` is called here because the lead/specialist prompts are built
at module-import time (before each agent's ``main()`` runs ``load_dotenv()``),
and the prompt builders need the flag.  ``load_dotenv`` is idempotent and does
not override variables already set in the environment.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

_TRUTHY = {"1", "true", "yes", "on"}


def memory_enabled() -> bool:
    """Return True when the Memory API should be used (Enterprise accounts)."""
    load_dotenv()
    return os.environ.get("BAND_ENABLE_MEMORY", "").strip().lower() in _TRUTHY
