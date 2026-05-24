from fastapi import APIRouter

from app.models.preference_models import UserPreferences
from app.services.preferences_store import load_preferences, save_preferences

router = APIRouter(tags=["preferences"])


@router.get("/preferences", response_model=UserPreferences)
def get_preferences() -> UserPreferences:
    return load_preferences()


@router.post("/preferences", response_model=UserPreferences)
def update_preferences(prefs: UserPreferences) -> UserPreferences:
    save_preferences(prefs)
    return prefs
