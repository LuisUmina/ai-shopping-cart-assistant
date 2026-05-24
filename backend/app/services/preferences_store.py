"""
Shared load/save helpers for user preferences.

Both routes_preferences (REST) and routes_chat (pipeline) need to read the
same persisted preferences. Keeping them in a single module avoids drift.
"""
from pathlib import Path

from app.models.preference_models import UserPreferences

_PREFS_FILE = Path(__file__).resolve().parents[2] / "data" / "user_preferences.json"


def load_preferences() -> UserPreferences:
    """Load user preferences from disk; return defaults if missing or invalid."""
    if _PREFS_FILE.exists():
        try:
            return UserPreferences.model_validate_json(
                _PREFS_FILE.read_text(encoding="utf-8")
            )
        except Exception:
            pass
    return UserPreferences()


def save_preferences(prefs: UserPreferences) -> None:
    """Persist user preferences to disk."""
    _PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PREFS_FILE.write_text(prefs.model_dump_json(indent=2), encoding="utf-8")
