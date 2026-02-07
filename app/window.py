from __future__ import annotations

import json
import re
import traceback
from pathlib import Path
from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.api_client import DeepSeekClient
from app.file_icons import icon_for_file
from app.models import ReviewResult, parse_review_json
from app.providers import get_provider
from app.settings import AppSettings, load_settings, save_settings
from app.settings_dialog import SettingsDialog
from app.theme import app_stylesheet
from app.widgets import CardWidget, CategoryChart, CodeEditor, FileCardWidget, score_color


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("代码检测")
        self.setMinimumSize(1080, 720)
        self.setStyleSheet(app_stylesheet())
        self._thread_pool = QThreadPool.globalInstance()
        self._settings = load_settings()
        self._opened_files: list[Path] = []
        self._file_contents: dict[str, str] = {}
        self._file_cards: dict[str, FileCardWidget] = {}
        self._selected_file_id: str = ""

        self._build_ui()
        self._render_placeholder("就绪。点击“开始检测”。")

    def _build_ui(self) -> None:
        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(10)
        title = QLabel("代码检测")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        top.addWidget(title, 1)

        self.settings_btn = QToolButton()
        self.settings_btn.setToolTip("设置")
        self.settings_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
        self.settings_btn.clicked.connect(self.open_settings)
        top.addWidget(self.settings_btn, 0)
        root_layout.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        open_btn = QPushButton("打开文件（可多选）")
        open_btn.setObjectName("secondaryBtn")
        open_btn.clicked.connect(self.open_files)
        btn_row.addWidget(open_btn, 0)

        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.clicked.connect(self.clear_code)
        btn_row.addWidget(clear_btn, 0)

        btn_row.addStretch(1)

        self.run_btn = QPushButton("开始检测")
        self.run_btn.clicked.connect(self.run_analysis)
        btn_row.addWidget(self.run_btn, 0)

        left_layout.addLayout(btn_row)

        self.files_scroll = QScrollArea()
        self.files_scroll.setWidgetResizable(True)
        self.files_scroll.setFixedHeight(170)
        self.files_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.files_scroll.setStyleSheet(
            """
            QScrollArea {
                background: rgba(255, 255, 255, 120);
                border: 1px solid rgba(191, 217, 242, 200);
                border-radius: 14px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 6px 2px 6px 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(47, 111, 228, 120);
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            """
        )
        self.files_host = QWidget()
        self.files_layout = QVBoxLayout(self.files_host)
        self.files_layout.setContentsMargins(10, 10, 10, 10)
        self.files_layout.setSpacing(10)
        self.files_scroll.setWidget(self.files_host)
        left_layout.addWidget(self.files_scroll, 0)

        self.code_edit = CodeEditor()
        self.code_edit.setPlaceholderText("粘贴或打开需要检测的代码…")
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mono.setPointSize(11)
        self.code_edit.setFont(mono)
        self.code_edit.setTabStopDistance(4 * self.code_edit.fontMetrics().horizontalAdvance(" "))
        self.code_edit.textChanged.connect(self._on_code_changed)
        left_layout.addWidget(self.code_edit, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.status_label = QLabel("就绪。点击“开始检测”。")
        self.status_label.setWordWrap(True)
        right_layout.addWidget(self.status_label, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.result_host = QWidget()
        self.result_layout = QVBoxLayout(self.result_host)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_layout.setSpacing(12)
        self.result_layout.addStretch(1)
        self.scroll.setWidget(self.result_host)
        right_layout.addWidget(self.scroll, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([620, 460])
        root_layout.addWidget(splitter, 1)

        self.setCentralWidget(root)

    def open_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "选择代码文件（可多选）", "", "All Files (*.*)")
        if not paths:
            return
        self._add_files([Path(p) for p in paths])

    def clear_code(self) -> None:
        self._opened_files = []
        self._file_contents = {}
        self._file_cards = {}
        self._selected_file_id = ""
        self._refresh_files_ui()
        self.code_edit.clear()
        self.status_label.setText("就绪。")
        self._clear_results()
        self._render_placeholder("就绪。点击“开始检测”。")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self._settings, parent=self)
        if dialog.exec():
            self._settings = dialog.settings()
            save_settings(self._settings)
            self.status_label.setText("设置已保存。")

    def run_analysis(self) -> None:
        self.status_label.setText("正在生成…")
        self._clear_results()
        self._render_placeholder("正在生成…")

        code = self._build_code_for_analysis().strip("\n")
        if not code.strip():
            QMessageBox.information(self, "提示", "请先粘贴或打开代码。")
            self.status_label.setText("未检测：没有代码。")
            return
        if not self._settings.api_key.strip():
            provider_name = get_provider(self._settings.provider).display_name
            QMessageBox.warning(self, "需要设置", f"请先在“设置”里填写 {provider_name} API Key。")
            self.status_label.setText("未检测：需要设置 API Key。")
            return
        self.run_btn.setEnabled(False)

        language_hint = guess_language(code)
        extra = ""
        if self._is_project_mode():
            extra = (
                "这是一个多文件项目，请额外检测跨文件连贯逻辑：\n"
                "- 调用链是否自洽、模块边界是否清晰\n"
                "- 命名/接口/数据结构是否一致\n"
                "- 重复逻辑与可复用点\n"
                "- 潜在循环依赖、耦合过高点\n"
                "请在 categories 增加维度：连贯性/跨文件逻辑、一致性/架构。"
            )
            language_hint = "多文件项目（可能多语言）"
        job = AnalyzeJob(code=code, language_hint=language_hint, settings=self._settings, extra_requirements=extra)
        job.signals.succeeded.connect(self._on_analysis_ok)
        job.signals.failed.connect(self._on_analysis_failed)
        job.signals.finished.connect(self._on_analysis_finished)
        self._thread_pool.start(job)

    def _on_analysis_ok(self, result: ReviewResult) -> None:
        self.status_label.setText(f"完成。总体分：{result.overall_score}/100")
        self._clear_results()
        self._render_result(result)

    def _on_analysis_failed(self, message: str) -> None:
        self.status_label.setText("失败。请检查网络/Key/模型。")
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("分析失败")
        provider_name = get_provider(self._settings.provider).display_name
        box.setText(f"调用 {provider_name} 进行分析失败。")
        box.setInformativeText("请检查网络、API Key、模型名称以及 Base URL。")
        box.setDetailedText(message)
        box.exec()

    def _on_analysis_finished(self) -> None:
        self.run_btn.setEnabled(True)

    def _clear_results(self) -> None:
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            w = item.widget() if item is not None else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _render_result(self, result: ReviewResult) -> None:
        overall = CardWidget("总体结论")
        overall.set_badge(f"{result.overall_score}", score_color(result.overall_score))
        overall.add_paragraph(result.overall_summary)
        metrics_text = _format_metrics(result.metrics)
        if metrics_text:
            overall.add_paragraph(metrics_text)
        self.result_layout.addWidget(overall)

        chart_card = CardWidget("维度分数图表")
        names = [c.name for c in result.categories]
        scores = [c.score for c in result.categories]
        avg_score = int(round(sum(scores) / len(scores))) if scores else 0
        chart_card.set_badge(f"{avg_score}", score_color(avg_score))
        chart = CategoryChart()
        chart.set_data(names, scores)
        chart_card.body.addWidget(chart)
        self.result_layout.addWidget(chart_card)

        for cat in result.categories:
            card = CardWidget(cat.name)
            card.set_badge(f"{cat.score}", score_color(cat.score))
            if cat.summary:
                card.add_paragraph(cat.summary)
            if cat.issues:
                card.add_paragraph("主要问题：")
                card.add_list(cat.issues)
            if cat.suggestions:
                card.add_paragraph("改进建议：")
                card.add_list(cat.suggestions)
            self.result_layout.addWidget(card)

        self.result_layout.addStretch(1)

    def _render_placeholder(self, text: str) -> None:
        placeholder = parse_review_json(
            {
                "overall_score": 0,
                "overall_summary": text,
                "metrics": {},
                "categories": [
                    {"name": "简洁性", "score": 0, "summary": "", "issues": [], "suggestions": []},
                    {"name": "可读性", "score": 0, "summary": "", "issues": [], "suggestions": []},
                    {"name": "复杂度", "score": 0, "summary": "", "issues": [], "suggestions": []},
                    {"name": "可维护性", "score": 0, "summary": "", "issues": [], "suggestions": []},
                    {"name": "风格一致性", "score": 0, "summary": "", "issues": [], "suggestions": []},
                    {"name": "潜在缺陷", "score": 0, "summary": "", "issues": [], "suggestions": []},
                    {"name": "安全性", "score": 0, "summary": "", "issues": [], "suggestions": []},
                ],
            }
        )
        self._render_result(placeholder)

    def _add_files(self, paths: list[Path]) -> None:
        added = 0
        for p in paths:
            try:
                resolved = p.resolve()
            except Exception:
                resolved = p
            if resolved in self._opened_files:
                continue
            try:
                text = resolved.read_text(encoding="utf-8")
            except Exception:
                text = resolved.read_text(encoding="utf-8", errors="replace")
            self._opened_files.append(resolved)
            self._file_contents[str(resolved)] = text
            added += 1
        self._refresh_files_ui()
        if added and not self._selected_file_id and self._opened_files:
            self._select_file(str(self._opened_files[0]))
        elif added and self._opened_files:
            self._select_file(str(self._opened_files[-1]))

    def _refresh_files_ui(self) -> None:
        for i in reversed(range(self.files_layout.count())):
            item = self.files_layout.itemAt(i)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._file_cards = {}

        if not self._opened_files:
            return

        for p in self._opened_files:
            fid = str(p)
            icon = icon_for_file(p)
            card = FileCardWidget(file_id=fid, title=p.name, icon=icon)
            card.clicked.connect(self._select_file)
            card.remove_requested.connect(self._remove_file)
            card.set_selected(fid == self._selected_file_id)
            self._file_cards[fid] = card
            self.files_layout.addWidget(card)
    def _select_file(self, file_id: str) -> None:
        if file_id not in self._file_contents:
            return
        self._selected_file_id = file_id
        for fid, card in self._file_cards.items():
            card.set_selected(fid == file_id)
        self.code_edit.blockSignals(True)
        self.code_edit.setPlainText(self._file_contents.get(file_id, ""))
        self.code_edit.blockSignals(False)
        self.status_label.setText(f"预览：{Path(file_id).name}")

    def _remove_file(self, file_id: str) -> None:
        if file_id not in self._file_contents:
            return
        self._opened_files = [p for p in self._opened_files if str(p) != file_id]
        self._file_contents.pop(file_id, None)
        self._file_cards.pop(file_id, None)
        removed_selected = self._selected_file_id == file_id
        if removed_selected:
            self._selected_file_id = ""
        self._refresh_files_ui()
        if removed_selected and self._opened_files:
            self._select_file(str(self._opened_files[0]))
        elif removed_selected:
            self.code_edit.blockSignals(True)
            self.code_edit.clear()
            self.code_edit.blockSignals(False)
            self.status_label.setText("就绪。")
            self._clear_results()
            self._render_placeholder("就绪。点击“开始检测”。")

    def _on_code_changed(self) -> None:
        if not self._selected_file_id:
            return
        self._file_contents[self._selected_file_id] = self.code_edit.toPlainText()

    def _is_project_mode(self) -> bool:
        return len(self._opened_files) > 1

    def _build_code_for_analysis(self) -> str:
        if self._is_project_mode():
            parts: list[str] = []
            for p in self._opened_files:
                fid = str(p)
                content = self._file_contents.get(fid, "")
                parts.append(f"### {p.name}\n{content}")
            return "\n\n".join(parts)
        return self.code_edit.toPlainText()


def _format_metrics(metrics: dict) -> str:
    lines = []
    if not isinstance(metrics, dict):
        return ""
    for key in ["lines", "functions", "classes", "complexity_hint"]:
        if key in metrics and metrics[key] not in (None, ""):
            lines.append(f"{key}: {metrics[key]}")
    return " | ".join(lines)


def guess_language(code: str) -> str:
    if re.search(r"^\s*def\s+\w+\(", code, flags=re.M) or "import " in code:
        return "Python"
    if re.search(r"^\s*function\s+\w+\(", code, flags=re.M) or "console.log" in code:
        return "JavaScript/TypeScript"
    if "#include" in code or re.search(r"\bstd::", code):
        return "C/C++"
    if "public class " in code or "System.out" in code:
        return "Java"
    if "package main" in code or "func " in code:
        return "Go"
    return "未知/自动"


class AnalyzeSignals(QObject):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()


class AnalyzeJob(QRunnable):
    def __init__(self, code: str, language_hint: str, settings: AppSettings, extra_requirements: str = "") -> None:
        super().__init__()
        self.code = code
        self.language_hint = language_hint
        self.settings = settings
        self.extra_requirements = extra_requirements
        self.signals = AnalyzeSignals()

    def run(self) -> None:
        try:
            client = DeepSeekClient(base_url=self.settings.base_url, api_key=self.settings.api_key)
            resp = client.analyze_code(
                code=self.code,
                language_hint=self.language_hint,
                model=self.settings.model,
                extra_requirements=self.extra_requirements,
            )
            payload = _safe_parse_json(resp.content_text)
            payload.setdefault("metrics", {})
            if isinstance(payload.get("metrics"), dict):
                payload["metrics"] = {**_local_metrics(self.code), **payload["metrics"]}
            result = parse_review_json(payload)
            self.signals.succeeded.emit(result)
        except Exception as e:
            detail = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            self.signals.failed.emit(detail)
        finally:
            self.signals.finished.emit()


def _local_metrics(code: str) -> dict:
    lines = [ln for ln in code.splitlines() if ln.strip()]
    functions = len(re.findall(r"^\s*def\s+\w+\(", code, flags=re.M)) + len(
        re.findall(r"^\s*(?:async\s+)?function\s+\w+\(", code, flags=re.M)
    )
    classes = len(re.findall(r"^\s*class\s+\w+", code, flags=re.M)) + len(
        re.findall(r"^\s*public\s+class\s+\w+", code, flags=re.M)
    )
    branch_tokens = len(re.findall(r"\b(if|elif|else if|for|while|case|catch|except)\b", code))
    if branch_tokens >= 40:
        complexity_hint = "高"
    elif branch_tokens >= 18:
        complexity_hint = "中"
    else:
        complexity_hint = "低"
    return {"lines": len(lines), "functions": functions, "classes": classes, "complexity_hint": complexity_hint}


def _safe_parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {"overall_score": 0, "overall_summary": "模型输出非JSON对象", "raw": obj}
    except Exception:
        extracted = _extract_json_object(text)
        if extracted:
            try:
                obj = json.loads(extracted)
                return obj if isinstance(obj, dict) else {"overall_score": 0, "overall_summary": "模型输出非JSON对象", "raw": obj}
            except Exception:
                pass
        return {"overall_score": 0, "overall_summary": "无法解析模型返回为JSON。", "raw_text": text}


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        return ""
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return ""
