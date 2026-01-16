from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import requests
from requests.auth import HTTPBasicAuth


@dataclass
class IntervalsClient:
    api_base: str
    api_token: str
    wellness_path: str
    athlete_id: str
    auth_mode: str = "basic"

    def _build_url(self, date: str) -> str:
        path = self.wellness_path.format(athlete_id=self.athlete_id, date=date)
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.api_base.rstrip('/')}{path}"

    def publish_wellness(self, payload: Dict[str, Any], date: str) -> Dict[str, Any]:
        url = self._build_url(date)
        headers = {"Content-Type": "application/json"}
        auth = None
        if self.auth_mode.lower() == "bearer":
            headers["Authorization"] = f"Bearer {self.api_token}"
        else:
            auth = HTTPBasicAuth("API_KEY", self.api_token)

        response = requests.put(
            url,
            headers=headers,
            auth=auth,
            json=payload,
            timeout=30,
        )
        if not response.ok:
            raise ValueError(
                f"Intervals API error {response.status_code}: {response.text}"
            )
        if response.content:
            return response.json()
        return {"status": "ok"}
