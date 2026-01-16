from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from .config import Config
from .fitbit_client import (
    FitbitClient,
    extract_avg_sleeping_hr,
    extract_hrv_rmssd,
    extract_resting_hr,
    extract_respiration,
    extract_sleep_minutes,
    extract_sleep_score,
    extract_spo2,
    extract_weight,
    extract_readiness,
)
from .intervals_client import IntervalsClient


@dataclass
class FitbitData:
    date: str
    summary: Dict[str, Any]
    sleep: Dict[str, Any]
    rhr: Optional[int]
    weight: Optional[float]
    sleep_score: Optional[float]
    avg_sleeping_hr: Optional[float]
    spo2: Optional[float]
    hrv_rmssd: Optional[float]
    readiness: Optional[float]
    respiration: Optional[float]


def _get_by_path(data: Dict[str, Any], path: str) -> Any:
    if path in data:
        return data[path]
    current: Any = data
    for segment in path.split("."):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        else:
            return None
    return current


def build_payload(config: Config, fitbit_data: FitbitData) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "date": fitbit_data.date,
        "summary": fitbit_data.summary,
        "sleep": {
            "minutes": extract_sleep_minutes(fitbit_data.sleep),
            "score": fitbit_data.sleep_score,
            "avg_hr": fitbit_data.avg_sleeping_hr,
            "raw": fitbit_data.sleep,
        },
        "rhr": fitbit_data.rhr,
        "weight": fitbit_data.weight,
        "spo2": fitbit_data.spo2,
        "hrv": {"rmssd": fitbit_data.hrv_rmssd},
        "readiness": fitbit_data.readiness,
        "respiration": fitbit_data.respiration,
    }

    payload: Dict[str, Any] = {}
    for target_field, source_path in config.intervals_field_map.items():
        value = _get_by_path(base, source_path)
        if value is not None:
            if target_field == "sleepSecs" and isinstance(value, (int, float)):
                value = int(value * 60)
            payload[target_field] = value

    return payload


def _update_env_refresh_token(new_refresh_token: str) -> None:
    try:
        with open(".env", "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except FileNotFoundError:
        return

    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("FITBIT_REFRESH_TOKEN="):
            new_lines.append(f"FITBIT_REFRESH_TOKEN={new_refresh_token}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"FITBIT_REFRESH_TOKEN={new_refresh_token}\n")

    with open(".env", "w", encoding="utf-8") as handle:
        handle.writelines(new_lines)


def publish_daily(config: Config, for_date: str) -> Dict[str, Any]:
    logger = logging.getLogger(__name__)
    fitbit = FitbitClient(
        client_id=config.fitbit_client_id,
        client_secret=config.fitbit_client_secret,
        refresh_token=config.fitbit_refresh_token,
        user_id=config.fitbit_user_id,
    )
    access_token, new_refresh = fitbit.refresh_access_token()
    if new_refresh and new_refresh != config.fitbit_refresh_token:
        _update_env_refresh_token(new_refresh)

    summary_payload = fitbit.get_daily_summary(access_token, for_date)
    sleep_payload = fitbit.get_sleep(access_token, for_date)
    heart_payload = fitbit.get_heart(access_token, for_date)
    weight_payload = fitbit.get_weight(access_token, for_date)
    sleep_score_payload = fitbit.get_sleep_score(access_token, for_date)
    spo2_payload = fitbit.get_spo2(access_token, for_date)
    hrv_payload = fitbit.get_hrv(access_token, for_date)
    readiness_payload = fitbit.get_readiness(access_token, for_date)
    respiration_payload = fitbit.get_respiration(access_token, for_date)

    logger.info("Fitbit summary payload:\n%s", json.dumps(summary_payload, indent=2))
    logger.info("Fitbit sleep payload:\n%s", json.dumps(sleep_payload, indent=2))
    logger.info("Fitbit heart payload:\n%s", json.dumps(heart_payload, indent=2))
    logger.info("Fitbit weight payload:\n%s", json.dumps(weight_payload, indent=2))
    logger.info(
        "Fitbit sleep score payload:\n%s",
        json.dumps(sleep_score_payload, indent=2),
    )
    logger.info("Fitbit SpO2 payload:\n%s", json.dumps(spo2_payload, indent=2))
    logger.info("Fitbit HRV payload:\n%s", json.dumps(hrv_payload, indent=2))
    logger.info(
        "Fitbit readiness payload:\n%s",
        json.dumps(readiness_payload, indent=2),
    )
    logger.info(
        "Fitbit respiration payload:\n%s",
        json.dumps(respiration_payload, indent=2),
    )

    fitbit_data = FitbitData(
        date=for_date,
        summary=summary_payload.get("summary", {}),
        sleep=sleep_payload,
        rhr=extract_resting_hr(heart_payload),
        weight=extract_weight(weight_payload),
        sleep_score=extract_sleep_score(sleep_score_payload),
        avg_sleeping_hr=extract_avg_sleeping_hr(sleep_payload),
        spo2=extract_spo2(spo2_payload),
        hrv_rmssd=extract_hrv_rmssd(hrv_payload),
        readiness=extract_readiness(readiness_payload),
        respiration=extract_respiration(respiration_payload),
    )

    intervals = IntervalsClient(
        api_base=config.intervals_api_base,
        api_token=config.intervals_api_token,
        wellness_path=config.intervals_wellness_path,
        athlete_id=config.intervals_athlete_id,
        auth_mode=config.intervals_auth_mode,
    )

    payload = build_payload(config, fitbit_data)
    return intervals.publish_wellness(payload, for_date)


def today_iso() -> str:
    return date.today().isoformat()
