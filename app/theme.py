from __future__ import annotations

import sys
from pathlib import Path


def _get_assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidate = base / "assets"
        if candidate.exists():
            return candidate
        return Path(sys.executable).parent / "assets"
    return Path(__file__).resolve().parent.parent / "assets"


def app_stylesheet() -> str:
    assets_dir = _get_assets_dir().as_posix()
    return """
    QWidget {
        background: #EAF4FF;
        color: #111111;
        font-size: 13px;
    }
    QLineEdit, QPlainTextEdit, QTextEdit, QComboBox {
        background: #FFFFFF;
        border: 1px solid #BFD9F2;
        border-radius: 8px;
        padding: 8px;
        selection-background-color: #3B82F6;
        selection-color: #FFFFFF;
    }
    /* 模型选择下拉：更清晰的下拉提示与轻量图标 */
    QComboBox {
        padding: 6px 34px 6px 10px;
        border-radius: 10px;
    }
    QComboBox:hover { border: 1px solid #7FB2F5; }
    QComboBox:focus { border: 1px solid #3B82F6; }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid #E1EEF9;
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
        background: #F5FAFF;
    }
    QComboBox::down-arrow {
        image: url(__ASSET_PATH__/icons/chevron-down.svg);
        width: 12px;
        height: 12px;
    }
    QComboBox::down-arrow:on { top: 1px; }
    QComboBox QAbstractItemView {
        background: #FFFFFF;
        border: 1px solid #BFD9F2;
        border-radius: 8px;
        selection-background-color: #DCEBFF;
        selection-color: #111111;
        padding: 4px;
    }
    QPushButton {
        background: #2F6FE4;
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 8px 12px;
    }
    QPushButton:hover { background: #2A63CC; }
    QPushButton:disabled { background: #9DB7E8; }
    QPushButton#secondaryBtn {
        background: #FFFFFF;
        color: #111111;
        border: 1px solid #BFD9F2;
    }
    QPushButton#secondaryBtn:hover { background: #F3F8FF; }
    QScrollArea { border: none; }
    QToolButton {
        background: transparent;
        border: none;
        padding: 6px;
    }
    QToolButton:hover {
        background: #D6E9FF;
        border-radius: 10px;
    }
    """.replace("__ASSET_PATH__", assets_dir)
