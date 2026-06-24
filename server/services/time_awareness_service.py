"""Time awareness — knows what day/hour/month/season it is."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def get_time_context() -> dict[str, Any]:
    now = datetime.now(timezone.utc).astimezone()
    hour = now.hour
    weekday = now.weekday()  # 0 = Monday
    day = now.day
    month = now.month

    WEEKS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    HOURS = {
        (0, 5): "凌晨",
        (5, 8): "早晨",
        (8, 12): "上午",
        (12, 14): "中午",
        (14, 18): "下午",
        (18, 21): "傍晚",
        (21, 24): "夜晚",
    }
    segment = next(v for (s, e), v in HOURS.items() if s <= hour < e)

    SEASONS = {12: "冬季", 1: "冬季", 2: "冬季", 3: "春季", 4: "春季", 5: "春季", 6: "夏季", 7: "夏季", 8: "夏季", 9: "秋季", 10: "秋季", 11: "秋季"}
    season = SEASONS.get(month, "")

    is_weekend = weekday >= 5
    is_month_end = day >= 25
    is_month_start = day <= 5
    is_quarter_end = month in {3, 6, 9, 12} and day >= 25

    notable_dates = {
        (6, 1): "Q2 开始", (6, 2): "Q2 第二天",
        (9, 1): "Q3 开始",
        (12, 1): "Q4 开始",
    }
    today_note = notable_dates.get((month, day), "")

    return {
        "date": now.strftime("%Y-%m-%d"),
        "weekday": WEEKS[weekday],
        "hour": hour,
        "segment": segment,
        "season": season,
        "is_weekend": is_weekend,
        "is_month_end": is_month_end,
        "is_month_start": is_month_start,
        "is_quarter_end": is_quarter_end,
        "today_note": today_note,
        "greeting": f"{segment}好" if not is_weekend else f"{segment}好，周末愉快",
    }
