from __future__ import annotations

import json
from typing import Any

import httpx

from app.agent.prompt import build_agent_prompt
from app.config import settings


class LLMClient:
    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model

    @property
    def is_enabled(self) -> bool:
        return bool(self.api_key)

    async def explain(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if not self.is_enabled:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://wasteiq.local",
            "X-Title": "WasteIQ",
        }
        body = {
            "model": self.model,
            "messages": build_agent_prompt(payload),
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=body,
                )
                response.raise_for_status()
        except httpx.HTTPError:
            return None

        content = response.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

