from __future__ import annotations

from enum import Enum


class SensitivityLevel(str, Enum):
    P0_PUBLIC = "P0_PUBLIC"
    P1_LOW = "P1_LOW"
    P2_MEDIUM = "P2_MEDIUM"
    P3_HIGH = "P3_HIGH"
    P4_SECRET = "P4_SECRET"


class ProfileType(str, Enum):
    watchlist = "watchlist"
    holding = "holding"
    project = "project"
    goal = "goal"
    preference = "preference"
    risk_profile = "risk_profile"
    personal_context = "personal_context"
