from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

FITBIT_API_BASE = "https://api.fitbit.com"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"


@dataclass
class FitbitClient:
    client_id: str
    client_secret: str
    refresh_token: str
    user_id: str = "-"

    def _basic_auth_header(self) -> str:
        token = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        return base64.b64encode(token).decode("utf-8")

    def refresh_access_token(self) -> tuple[str, str | None]:
        headers = {
            "Authorization": f"Basic {self._basic_auth_header()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "client_id": self.client_id,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        response = requests.post(FITBIT_TOKEN_URL, headers=headers, data=data, timeout=30)
        if not response.ok:
            raise ValueError(
                f"Fitbit token refresh error {response.status_code}: {response.text}"
            )
        payload = response.json()
        access_token = payload.get("access_token")
        if not access_token:
            raise ValueError("Fitbit token refresh did not return access_token")
        return access_token, payload.get("refresh_token")

    def _get(self, access_token: str, path: str) -> Dict[str, Any]:
        url = f"{FITBIT_API_BASE}{path}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def _get_optional(self, access_token: str, path: str) -> Optional[Dict[str, Any]]:
        url = f"{FITBIT_API_BASE}{path}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code in {403, 404}:
            return None
        response.raise_for_status()
        return response.json()

    def get_daily_summary(self, access_token: str, date: str) -> Dict[str, Any]:
        return self._get(
            access_token, f"/1/user/{self.user_id}/activities/date/{date}.json"
        )

    def get_sleep(self, access_token: str, date: str) -> Dict[str, Any]:
        return self._get(access_token, f"/1.2/user/{self.user_id}/sleep/date/{date}.json")

    def get_heart(self, access_token: str, date: str) -> Dict[str, Any]:
        return self._get(
            access_token,
            f"/1/user/{self.user_id}/activities/heart/date/{date}/1d.json",
        )

    def get_weight(self, access_token: str, date: str) -> Optional[Dict[str, Any]]:
        return self._get_optional(
            access_token,
            f"/1/user/{self.user_id}/body/log/weight/date/{date}.json",
        )

    def get_sleep_score(self, access_token: str, date: str) -> Optional[Dict[str, Any]]:
        return self._get_optional(
            access_token,
            f"/1.2/user/{self.user_id}/sleep/score/date/{date}.json",
        )

    def get_spo2(self, access_token: str, date: str) -> Optional[Dict[str, Any]]:
        return self._get_optional(
            access_token,
            f"/1/user/{self.user_id}/spo2/date/{date}.json",
        )

    def get_hrv(self, access_token: str, date: str) -> Optional[Dict[str, Any]]:
        return self._get_optional(
            access_token,
            f"/1/user/{self.user_id}/hrv/date/{date}.json",
        )

    def get_readiness(self, access_token: str, date: str) -> Optional[Dict[str, Any]]:
        return self._get_optional(
            access_token,
            f"/1/user/{self.user_id}/readiness/date/{date}.json",
        )

    def get_respiration(self, access_token: str, date: str) -> Optional[Dict[str, Any]]:
        return self._get_optional(
            access_token,
            f"/1/user/{self.user_id}/br/date/{date}.json",
        )


def extract_resting_hr(heart_payload: Dict[str, Any]) -> Optional[int]:
    activities = heart_payload.get("activities-heart") or []
    if not activities:
        return None
    value = activities[0].get("value") or {}
    rhr = value.get("restingHeartRate")
    if isinstance(rhr, int):
        return rhr
    return None


def extract_sleep_minutes(sleep_payload: Dict[str, Any]) -> Optional[int]:
    summary = sleep_payload.get("summary") or {}
    minutes = summary.get("totalMinutesAsleep")
    if isinstance(minutes, int):
        return minutes
    return None


def extract_weight(weight_payload: Optional[Dict[str, Any]]) -> Optional[float]:
    if not weight_payload:
        return None
    entries = weight_payload.get("weight") or []
    for entry in reversed(entries):
        value = entry.get("weight")
        if isinstance(value, (int, float)):
            return float(value)
    return None


def extract_sleep_score(score_payload: Optional[Dict[str, Any]]) -> Optional[float]:
    if not score_payload:
        return None
    score_data = score_payload.get("sleepScore")
    if isinstance(score_data, dict):
        score = score_data.get("score")
        if isinstance(score, (int, float)):
            return float(score)
    if isinstance(score_data, list):
        for entry in score_data:
            score = entry.get("score")
            if isinstance(score, (int, float)):
                return float(score)
    if isinstance(score_payload.get("score"), (int, float)):
        return float(score_payload["score"])
    return None


def extract_avg_sleeping_hr(sleep_payload: Dict[str, Any]) -> Optional[float]:
    records = sleep_payload.get("sleep") or []
    for record in records:
        for key in ("averageHeartRate", "avgHeartRate", "heartRate"):
            value = record.get(key)
            if isinstance(value, (int, float)):
                return float(value)
    summary = sleep_payload.get("summary") or {}
    for key in ("averageHeartRate", "avgHeartRate"):
        value = summary.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def extract_spo2(spo2_payload: Optional[Dict[str, Any]]) -> Optional[float]:
    if not spo2_payload:
        return None
    values = spo2_payload.get("value") or spo2_payload.get("spo2")
    if isinstance(values, list):
        for entry in values:
            value = entry.get("value")
            if isinstance(value, dict):
                avg = value.get("avg")
                if isinstance(avg, (int, float)):
                    return float(avg)
            if isinstance(value, (int, float)):
                return float(value)
    if isinstance(values, dict):
        avg = values.get("avg")
        if isinstance(avg, (int, float)):
            return float(avg)
    if isinstance(spo2_payload.get("avg"), (int, float)):
        return float(spo2_payload["avg"])
    return None


def extract_hrv_rmssd(hrv_payload: Optional[Dict[str, Any]]) -> Optional[float]:
    if not hrv_payload:
        return None
    values = hrv_payload.get("hrv") or hrv_payload.get("value")
    if isinstance(values, list):
        for entry in values:
            value = entry.get("value")
            if isinstance(value, dict):
                rmssd = value.get("rmssd")
                if isinstance(rmssd, (int, float)):
                    return float(rmssd)
    if isinstance(values, dict):
        rmssd = values.get("rmssd")
        if isinstance(rmssd, (int, float)):
            return float(rmssd)
    return None


def extract_readiness(readiness_payload: Optional[Dict[str, Any]]) -> Optional[float]:
    if not readiness_payload:
        return None
    data = readiness_payload.get("dailyReadiness") or readiness_payload.get("readiness")
    if isinstance(data, list):
        for entry in data:
            score = entry.get("score")
            if isinstance(score, (int, float)):
                return float(score)
    if isinstance(data, dict):
        score = data.get("score")
        if isinstance(score, (int, float)):
            return float(score)
    if isinstance(readiness_payload.get("score"), (int, float)):
        return float(readiness_payload["score"])
    return None


def extract_respiration(respiration_payload: Optional[Dict[str, Any]]) -> Optional[float]:
    if not respiration_payload:
        return None
    values = respiration_payload.get("br") or respiration_payload.get("value")
    if isinstance(values, list):
        for entry in values:
            value = entry.get("value")
            if isinstance(value, dict):
                rate = value.get("breathingRate")
                if isinstance(rate, (int, float)):
                    return float(rate)
            if isinstance(value, (int, float)):
                return float(value)
    if isinstance(values, dict):
        rate = values.get("breathingRate")
        if isinstance(rate, (int, float)):
            return float(rate)
    return None
