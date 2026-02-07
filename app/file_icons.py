from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QIcon


def _get_assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidate = base / "assets"
        if candidate.exists():
            return candidate
        return Path(sys.executable).parent / "assets"
    return Path(__file__).resolve().parent.parent / "assets"


def icon_for_file(path: Path) -> QIcon:
    ext = path.suffix.lower().lstrip(".")
    name = _map_ext_to_icon_name(ext)
    icon_path = _get_assets_dir() / "icons" / f"{name}.svg"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


def _map_ext_to_icon_name(ext: str) -> str:
    if ext in {"py", "pyw"}:
        return "python"
    if ext in {"js", "ts", "tsx", "jsx"}:
        return "javascript"
    if ext in {"java"}:
        return "java"
    if ext in {"go"}:
        return "go"
    if ext in {"c", "h", "cpp", "hpp", "cc", "cxx"}:
        return "cpp"
    if ext in {"rs"}:
        return "rust"
    return "file"
