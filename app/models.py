from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CategoryResult:
    name: str
    score: int
    summary: str = ""
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReviewResult:
    overall_score: int
    overall_summary: str
    categories: list[CategoryResult]
    metrics: dict[str, Any] = field(default_factory=dict)
    raw_json: dict[str, Any] = field(default_factory=dict)


def clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        num = int(value)
    except Exception:
        return default
    return max(low, min(high, num))


def parse_review_json(payload: dict[str, Any]) -> ReviewResult:
    overall_score = clamp_int(payload.get("overall_score"), 0, 100, 0)
    overall_summary = str(payload.get("overall_summary") or "").strip()
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}

    categories_raw = payload.get("categories")
    categories: list[CategoryResult] = []
    if isinstance(categories_raw, list):
        for item in categories_raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip() or "未命名"
            score = clamp_int(item.get("score"), 0, 100, 0)
            summary = str(item.get("summary") or "").strip()
            issues = [str(x) for x in item.get("issues", []) if isinstance(x, (str, int, float))]
            suggestions = [str(x) for x in item.get("suggestions", []) if isinstance(x, (str, int, float))]
            categories.append(
                CategoryResult(
                    name=name,
                    score=score,
                    summary=summary,
                    issues=issues,
                    suggestions=suggestions,
                )
            )

    if not categories:
        for name in ["简洁性", "可读性", "复杂度", "可维护性", "风格一致性", "潜在缺陷", "安全性"]:
            categories.append(CategoryResult(name=name, score=0, summary=""))

    if not overall_summary:
        overall_summary = "未返回总体总结（可能是模型输出非结构化内容或网络异常）。"

    return ReviewResult(
        overall_score=overall_score,
        overall_summary=overall_summary,
        categories=categories,
        metrics=metrics,
        raw_json=payload,
    )
