from __future__ import annotations

import json
import shutil
from pathlib import Path

from server.schemas.profile_schemas import UserProfile


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "data" / "user_profile.example.json"
LOCAL = ROOT / "data" / "user_profile.local.json"
def _profiles_dir() -> Path:
    return ROOT / "data" / "user_profiles"

EMPTY_PROFILE = {
    "watchlist": [],
    "holdings": [],
    "projects": [],
    "preferences": {
        "answer_style": "",
        "risk_tolerance": "",
        "forbidden_advice": [],
    },
}


def _profile_path(user_id: str) -> Path:
    if user_id in ("default_user", ""):
        return LOCAL
    pd = _profiles_dir()
    pd.mkdir(parents=True, exist_ok=True)
    return pd / f"{user_id}.json"


def ensure_profile_files() -> None:
    EXAMPLE.parent.mkdir(parents=True, exist_ok=True)
    if not EXAMPLE.exists():
        EXAMPLE.write_text(json.dumps(EMPTY_PROFILE, ensure_ascii=False, indent=2), encoding="utf-8")
    if not LOCAL.exists():
        shutil.copyfile(EXAMPLE, LOCAL)


def load_user_profile(user_id: str = "") -> UserProfile:
    ensure_profile_files()
    path = _profile_path(user_id)
    if not path.exists():
        path.write_text(json.dumps(EMPTY_PROFILE, ensure_ascii=False, indent=2), encoding="utf-8")
    return UserProfile.model_validate_json(path.read_text(encoding="utf-8"))


def sanitized_profile_summary(user_id: str = "") -> dict:
    profile = load_user_profile(user_id)
    return {
        "watchlist": [
            {"symbol": item.symbol, "name": item.name, "market": item.market, "why_follow": item.why_follow}
            for item in profile.watchlist
        ],
        "holdings_summary": [
            {
                "market": item.market,
                "asset_type": "confirmed_holding",
                "name": item.name,
                "risk_tolerance": item.risk_tolerance or "未确认",
            }
            for item in profile.holdings
        ],
        "projects": profile.projects,
        "preferences": profile.preferences,
    }
