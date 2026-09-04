"""
Pytest configuration and shared fixtures for backend tests.

This conftest stubs out heavy/optional third-party dependencies (google.genai,
livekit, watchdog, bson, dotenv) and the not-yet-implemented `core.database`
module so that pure functions in the service layer can be imported and unit
tested in isolation without any network, database, or API calls.

The stubs are installed in sys.modules *before* any test module imports the
service packages, so the service modules pick up the stubs at import time.
"""

import sys
import os
import types as _pytypes
from unittest.mock import MagicMock

# Ensure the backend root is importable as a package root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def _make_module(name):
    """Create and register a stub module under the given dotted name."""
    mod = MagicMock(name=name)
    mod.__name__ = name
    mod.__all__ = []
    sys.modules[name] = mod
    return mod


def _install_stubs():
    """Install stub modules for optional/heavy dependencies."""
    # --- google.* (Gemini SDK) ---
    google = _make_module("google")
    genai = _make_module("google.genai")
    genai_types = _make_module("google.genai.types")

    # Make `from google import genai` work
    google.genai = genai
    # Make `from google.genai import types` work
    genai.types = genai_types

    # Provide minimal type-like attributes used by schema builders
    genai_types.Type = MagicMock(
        OBJECT="OBJECT",
        STRING="STRING",
        INTEGER="INTEGER",
        NUMBER="NUMBER",
        BOOLEAN="BOOLEAN",
        ARRAY="ARRAY",
    )
    genai_types.Schema = MagicMock(side_effect=lambda **kwargs: kwargs)
    genai_types.Content = MagicMock(side_effect=lambda **kwargs: kwargs)
    genai_types.Part = MagicMock()
    genai_types.Part.from_text = MagicMock(side_effect=lambda text: {"text": text})
    genai_types.GenerateContentConfig = MagicMock(side_effect=lambda **kwargs: kwargs)
    genai_types.ThinkingConfig = MagicMock(side_effect=lambda **kwargs: kwargs)

    genai.Client = MagicMock()
    genai.types = genai_types

    # --- livekit.* (telephony SDK) ---
    livekit = _make_module("livekit")
    livekit_api = _make_module("livekit.api")
    livekit_agents = _make_module("livekit.agents")
    livekit_plugins = _make_module("livekit.plugins")
    livekit_plugins_turn_detector_english = _make_module(
        "livekit.plugins.turn_detector.english"
    )
    livekit_plugins_turn_detector_multilingual = _make_module(
        "livekit.plugins.turn_detector.multilingual"
    )

    livekit.api = livekit_api
    livekit.agents = livekit_agents
    livekit.plugins = livekit_plugins
    livekit_plugins.turn_detector = MagicMock()
    livekit_plugins.turn_detector.english = livekit_plugins_turn_detector_english
    livekit_plugins.turn_detector.multilingual = (
        livekit_plugins_turn_detector_multilingual
    )
    livekit_plugins_turn_detector_english.EnglishModel = MagicMock()
    livekit_plugins_turn_detector_multilingual.MultilingualModel = MagicMock()

    livekit_api.LiveKitAPI = MagicMock()
    livekit_api.CreateAgentDispatchRequest = MagicMock()
    livekit_api.CreateSIPParticipantRequest = MagicMock()
    livekit_api.DeleteRoomRequest = MagicMock()
    livekit_api.TwirpError = type("TwirpError", (Exception,), {})

    livekit.rtc = MagicMock()
    livekit_agents.Agent = MagicMock()
    livekit_agents.AgentSession = MagicMock()
    livekit_agents.JobContext = MagicMock()
    livekit_agents.RunContext = MagicMock()
    livekit_agents.WorkerOptions = MagicMock()
    livekit_agents.RoomInputOptions = MagicMock()
    livekit_agents.function_tool = lambda *a, **k: (lambda fn: fn)
    livekit_agents.get_job_context = MagicMock()
    livekit_agents.cli = MagicMock()

    # --- watchdog.* (file system watcher) ---
    watchdog = _make_module("watchdog")
    watchdog_observers = _make_module("watchdog.observers")
    watchdog_events = _make_module("watchdog.events")
    watchdog.observers = watchdog_observers
    watchdog.events = watchdog_events
    watchdog_observers.Observer = MagicMock()
    watchdog_events.FileSystemEventHandler = object
    watchdog_events.FileCreatedEvent = MagicMock()

    # --- bson ---
    bson = _make_module("bson")
    bson.ObjectId = MagicMock(side_effect=lambda x: x)

    # --- dotenv ---
    dotenv = _make_module("dotenv")
    dotenv.load_dotenv = MagicMock()

    # --- core.database (referenced by services but not implemented) ---
    # NOTE: `core` itself is a real package in this repo, so we must NOT
    # replace it with a stub. We only inject the missing `core.database`
    # submodule as a stub so that `from core import database` / 
    # `from core.database import ...` works at import time.
    import importlib
    core_real = importlib.import_module("core")
    core_database = _make_module("core.database")
    core_real.database = core_database


_install_stubs()


import pytest


@pytest.fixture
def reset_gemini_singleton():
    """Reset the global Gemini client singleton between tests if present."""
    try:
        import core.gemini_client as gc
        old = gc._gemini_client
        gc._gemini_client = None
        yield
        gc._gemini_client = old
    except Exception:
        yield
