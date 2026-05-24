from pathlib import Path

from fastapi import APIRouter

from app.models.preference_models import UserPreferences

router = APIRouter(tags=["preferences"])

_PREFS_FILE = Path(__file__).resolve().parents[3] / "data" / "user_preferences.json"


def _load() -> UserPreferences:
    if _PREFS_FILE.exists():
        try:
            return UserPreferences.model_validate_json(_PREFS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return UserPreferences()


def _save(prefs: UserPreferences) -> None:
    _PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PREFS_FILE.write_text(prefs.model_dump_json(indent=2), encoding="utf-8")


@router.get("/preferences", response_model=UserPreferences)
def get_preferences() -> UserPreferences:
    return _load()


@router.post("/preferences", response_model=UserPreferences)
def update_preferences(prefs: UserPreferences) -> UserPreferences:
    _save(prefs)
    return prefs
