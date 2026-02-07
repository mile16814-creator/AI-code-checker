from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPlainTextEdit,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


def score_color(score: int) -> str:
    if score >= 85:
        return "#10B981"
    if score >= 70:
        return "#22C55E"
    if score >= 55:
        return "#F59E0B"
    if score >= 40:
        return "#F97316"
    return "#EF4444"


class CardWidget(QFrame):
    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(
            """
            QFrame#card {
                background: #FFFFFF;
                border: 1px solid #CFE3F7;
                border-radius: 14px;
            }
            """
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)
        self.title_label = QLabel(title)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setWordWrap(True)
        header.addWidget(self.title_label, 1)
        self.badge_label = QLabel("")
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label.setMinimumWidth(54)
        self.badge_label.setStyleSheet(
            "background: #EEF6FF; border: 1px solid #CFE3F7; border-radius: 10px; padding: 4px 8px;"
        )
        header.addWidget(self.badge_label, 0)
        layout.addLayout(header)

        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        layout.addLayout(self.body)

    def set_badge(self, text: str, color: str = "#111111") -> None:
        self.badge_label.setText(text)
        self.badge_label.setStyleSheet(
            f"background: #EEF6FF; border: 1px solid #CFE3F7; border-radius: 10px; padding: 4px 8px; color: {color};"
        )

    def add_paragraph(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.body.addWidget(label)
        return label

    def add_list(self, items: list[str], prefix: str = "• ") -> QLabel:
        if not items:
            label = QLabel("（无）")
            self.body.addWidget(label)
            return label
        html = "<br/>".join([f"{prefix}{_escape(x)}" for x in items])
        label = QLabel(html)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.body.addWidget(label)
        return label


class ScoreBar(QWidget):
    def __init__(self, label: str, score: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.name = QLabel(label)
        self.name.setWordWrap(True)
        layout.addWidget(self.name)
        row = QHBoxLayout()
        row.setSpacing(10)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(max(0, min(100, int(score))))
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(10)
        color = score_color(score)
        self.bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: #EEF6FF;
                border: 1px solid #CFE3F7;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 6px;
            }}
            """
        )
        row.addWidget(self.bar, 1)
        self.value = QLabel(f"{int(score)}")
        self.value.setMinimumWidth(36)
        self.value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.value.setStyleSheet(f"color: {color}; font-weight: 600;")
        row.addWidget(self.value, 0)
        layout.addLayout(row)


class ColorBarChart(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._names: list[str] = []
        self._scores: list[int] = []
        self.setMinimumHeight(260)

    def set_data(self, names: list[str], scores: list[int]) -> None:
        self._names = [str(x) for x in names]
        self._scores = [max(0, min(100, int(s))) for s in scores]
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        outer = self.rect().adjusted(10, 10, -10, -10)
        painter.fillRect(outer, QColor("#FFFFFF"))

        if not self._names or not self._scores:
            painter.setPen(QColor("#35506B"))
            painter.drawText(outer, Qt.AlignmentFlag.AlignCenter, "无图表数据")
            return

        n = min(len(self._names), len(self._scores))
        names = self._names[:n]
        scores = self._scores[:n]

        fm = painter.fontMetrics()
        label_w = min(220, max(80, max(fm.horizontalAdvance(x) for x in names) + 8))
        value_w = 42
        gap = 10

        chart_rect = outer.adjusted(label_w + gap, 8, -value_w - gap, -8)
        row_h = max(24, int(chart_rect.height() / max(1, n)))
        bar_h = max(10, int(row_h * 0.45))

        grid_pen = QPen(QColor("#D8E9FB"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for t in [0, 50, 100]:
            x = chart_rect.left() + int(chart_rect.width() * (t / 100))
            painter.drawLine(x, chart_rect.top(), x, chart_rect.bottom())

        for i, (name, score) in enumerate(zip(names, scores)):
            y = chart_rect.top() + i * row_h + int((row_h - bar_h) / 2)

            painter.setPen(QColor("#111111"))
            painter.drawText(outer.left(), y, label_w, bar_h, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name)

            bar_w = int(chart_rect.width() * (score / 100))
            color = QColor(score_color(score))
            painter.fillRect(chart_rect.left(), y, bar_w, bar_h, color)

            painter.setPen(QColor("#BFD9F2"))
            painter.drawRect(chart_rect.left(), y, chart_rect.width(), bar_h)

            painter.setPen(color)
            painter.drawText(
                chart_rect.right() + gap,
                y,
                value_w,
                bar_h,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                str(score),
            )


class CategoryChart(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self._chart = ColorBarChart(self)
        root.addWidget(self._chart)

    def set_data(self, names: list[str], scores: list[int]) -> None:
        self._chart.set_data(names, scores)


class CodeEditor(QPlainTextEdit):
    def contextMenuEvent(self, event) -> None:
        menu = self.createStandardContextMenu()
        for action in menu.actions():
            text = action.text().replace("&", "")
            if "Undo" in text:
                action.setText("撤销")
            elif "Redo" in text:
                action.setText("重做")
            elif "Cut" in text:
                action.setText("剪切")
            elif "Copy" in text:
                action.setText("复制")
            elif "Paste" in text:
                action.setText("粘贴")
            elif "Delete" in text:
                action.setText("删除")
            elif "Select All" in text:
                action.setText("全选")
        menu.exec(event.globalPos())


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


class FileCardWidget(QFrame):
    clicked = pyqtSignal(str)
    remove_requested = pyqtSignal(str)

    def __init__(self, file_id: str, title: str, icon, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._file_id = file_id
        self.setObjectName("fileCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())
        self.setStyleSheet(
            """
            QFrame#fileCard {
                background: #FFFFFF;
                border: 1px solid #CFE3F7;
                border-radius: 12px;
            }
            QFrame#fileCard[selected="true"] {
                background: #E6F2FF;
                border: 1px solid #76B2F5;
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        icon_box = QFrame(self)
        icon_box.setObjectName("iconBox")
        icon_box.setFixedSize(28, 28)
        icon_box.setStyleSheet(
            "QFrame#iconBox { background: transparent; border: 1px solid #76B2F5; border-radius: 6px; }"
        )
        ib_layout = QHBoxLayout(icon_box)
        ib_layout.setContentsMargins(4, 4, 4, 4)
        ib_layout.setSpacing(0)
        self.icon_label = QLabel(icon_box)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(icon.pixmap(18, 18))
        ib_layout.addWidget(self.icon_label, 1)
        layout.addWidget(icon_box, 0)

        self.title_label = QLabel(title, self)
        self.title_label.setWordWrap(False)
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.title_label.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.title_label.installEventFilter(self)
        layout.addWidget(self.title_label, 1)

        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._file_id)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event) -> None:  # type: ignore[override]
        self._show_context_menu(event.globalPos())

    def eventFilter(self, obj, event) -> bool:  # type: ignore[override]
        if obj is self.title_label and event.type() == QEvent.Type.ContextMenu:
            self._show_context_menu(event.globalPos())
            return True
        return super().eventFilter(obj, event)

    def _show_context_menu(self, global_pos) -> None:
        menu = QMenu(self)
        copy_name_action = menu.addAction("复制文件名")
        menu.addSeparator()
        remove_action = menu.addAction("移出检测")
        action = menu.exec(global_pos)
        if action == remove_action:
            self.remove_requested.emit(self._file_id)
        elif action == copy_name_action:
            QApplication.clipboard().setText(self.title_label.text())
