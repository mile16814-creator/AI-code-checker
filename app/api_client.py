from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import requests


@dataclass(frozen=True)
class DeepSeekResponse:
    content_text: str
    raw: dict[str, Any]


def _is_v1_base_url(base_url: str) -> bool:
    try:
        p = urlparse(base_url.strip())
        return p.path.rstrip("/").endswith("/v1")
    except Exception:
        return False


def _endpoint(base_url: str, path_under_v1: str) -> str:
    base = (base_url or "").strip()
    if not base:
        raise ValueError("Base URL 不能为空")
    base = base.rstrip("/") + "/"
    if _is_v1_base_url(base):
        return urljoin(base, path_under_v1.lstrip("/"))
    return urljoin(base, f"v1/{path_under_v1.lstrip('/')}")


class OpenAICompatClient:
    def __init__(self, base_url: str, api_key: str, timeout_s: int = 60) -> None:
        self._base_url = base_url.rstrip("/") + "/"
        self._api_key = api_key.strip()
        self._timeout_s = timeout_s

    def analyze_code(self, code: str, language_hint: str, model: str, extra_requirements: str = "") -> DeepSeekResponse:
        url = _endpoint(self._base_url, "chat/completions")
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        body = {
            "model": model,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是资深代码审查与代码质量分析助手。你只输出 JSON，不能输出任何解释性文字。"
                        "输出必须可被 json.loads 直接解析。分数范围 0-100，越高越好。"
                    ),
                },
                {
                    "role": "user",
                    "content": _build_user_prompt(code=code, language_hint=language_hint, extra_requirements=extra_requirements),
                },
            ],
        }
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=self._timeout_s)
        resp.raise_for_status()
        raw = resp.json()
        content_text = ""
        try:
            content_text = raw["choices"][0]["message"]["content"]
        except Exception:
            content_text = json.dumps(raw, ensure_ascii=False)
        return DeepSeekResponse(content_text=content_text, raw=raw)

    def list_models(self) -> list[str]:
        url = _endpoint(self._base_url, "models")
        headers = {"Authorization": f"Bearer {self._api_key}"}
        resp = requests.get(url, headers=headers, timeout=self._timeout_s)
        resp.raise_for_status()
        raw = resp.json()
        items = raw.get("data", [])
        if not isinstance(items, list):
            return []
        model_ids: list[str] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            mid = it.get("id")
            if isinstance(mid, str) and mid.strip():
                model_ids.append(mid.strip())
        uniq = sorted(set(model_ids))
        return uniq


DeepSeekClient = OpenAICompatClient

def _build_user_prompt(code: str, language_hint: str, extra_requirements: str) -> str:
    schema = {
        "overall_score": 0,
        "overall_summary": "一句话总结优缺点",
        "metrics": {"lines": 0, "functions": 0, "classes": 0, "complexity_hint": "低/中/高"},
        "metrics": {"lines": 0, "functions": 0, "classes": 0, "complexity_hint": "低/中/高"},
        "categories": [
            {
                "name": "简洁性",
                "score": 0,
                "summary": "简短说明",
                "issues": ["问题1", "问题2"],
                "suggestions": ["建议1", "建议2"],
            }
        ],
    }
    extra = (extra_requirements or "").strip()
    extra_block = f"\n额外要求：\n{extra}\n" if extra else ""
    return (
        f"语言提示：{language_hint}\n"
        "请按以下 JSON 结构输出结果（字段名保持一致，categories 至少 5 项），不要输出多余文本：\n"
        f"{json.dumps(schema, ensure_ascii=False)}\n\n"
        "检测维度建议包含：简洁性、可读性、复杂度、可维护性、风格一致性、潜在缺陷/边界情况、安全性。\n"
        f"{extra_block}"
        "issues/suggestions 尽量具体到代码片段或模式，但不要粘贴整段代码。\n\n"
        "待检测代码如下：\n"
        "```text\n"
        f"{code}\n"
        "```"
    )
