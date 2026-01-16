from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class Config:
    fitbit_client_id: str
    fitbit_client_secret: str
    fitbit_refresh_token: str
    fitbit_user_id: str
    intervals_api_base: str
    intervals_api_token: str
    intervals_athlete_id: str
    intervals_wellness_path: str
    intervals_auth_mode: str
    intervals_field_map: Dict[str, str]


DEFAULT_FIELD_MAP = {
    "weight": "weight",
    "restingHR": "rhr",
    "sleepSecs": "sleep.minutes",
    "sleepScore": "sleep.score",
    "avgSleepingHR": "sleep.avg_hr",
    "spO2": "spo2",
    "hrv": "hrv.rmssd",
    "readiness": "readiness",
    "respiration": "respiration",
    "steps": "summary.steps",
    "kcalConsumed": "summary.caloriesOut",
}


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_config() -> Config:
    field_map_raw = os.getenv("INTERVALS_FIELD_MAP_JSON", "").strip()
    if field_map_raw:
        field_map = json.loads(field_map_raw)
    else:
        field_map = DEFAULT_FIELD_MAP

    return Config(
        fitbit_client_id=_env("FITBIT_CLIENT_ID"),
        fitbit_client_secret=_env("FITBIT_CLIENT_SECRET"),
        fitbit_refresh_token=_env("FITBIT_REFRESH_TOKEN"),
        fitbit_user_id=os.getenv("FITBIT_USER_ID", "-"),
        intervals_api_base=_env("INTERVALS_API_BASE", "https://intervals.icu"),
        intervals_api_token=_env("INTERVALS_API_TOKEN"),
        intervals_athlete_id=_env("INTERVALS_ATHLETE_ID"),
        intervals_wellness_path=os.getenv(
            "INTERVALS_WELLNESS_PATH",
            "/api/v1/athlete/{athlete_id}/wellness/{date}",
        ),
        intervals_auth_mode=os.getenv("INTERVALS_AUTH_MODE", "basic"),
        intervals_field_map=field_map,
    )
