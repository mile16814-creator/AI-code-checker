from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.providers import PROVIDERS, get_provider
from app.settings import AppSettings, settings_path, settings_store


class SettingsDialog(QDialog):
    def __init__(self, initial: AppSettings, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setModal(True)
        self.setMinimumWidth(520)
        self._draft: dict[str, tuple[str, str, str]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.provider = QComboBox()
        self._provider_index: dict[str, int] = {}
        for idx, p in enumerate(PROVIDERS):
            self.provider.addItem(p.display_name, p.provider_id)
            self._provider_index[p.provider_id] = idx
        form.addRow("API 厂商", self.provider)

        self.api_key = QLineEdit(initial.api_key)
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("sk-...（仅保存在本机配置文件）")
        self.api_key_btn = QPushButton("显示")
        self.api_key_btn.setObjectName("secondaryBtn")
        self.api_key_btn.setFixedWidth(88)
        self.api_key_btn.clicked.connect(self._toggle_api_key_visible)
        api_key_row = QWidget()
        api_key_row_layout = QHBoxLayout(api_key_row)
        api_key_row_layout.setContentsMargins(0, 0, 0, 0)
        api_key_row_layout.setSpacing(8)
        api_key_row_layout.addWidget(self.api_key, 1)
        api_key_row_layout.addWidget(self.api_key_btn, 0)
        form.addRow("API Key", api_key_row)

        self.base_url = QLineEdit(initial.base_url)
        self.base_url.setPlaceholderText("https://api.deepseek.com")
        form.addRow("Base URL", self.base_url)

        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.setCurrentText(initial.model)
        form.addRow("模型", self.model)

        layout.addLayout(form)

        info = QLabel(f"配置文件：{settings_path()}")
        info.setStyleSheet("color: #35506B;")
        info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info.setWordWrap(True)
        layout.addWidget(info)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.provider.currentIndexChanged.connect(self._on_provider_changed)
        self._set_provider(initial.provider)
        self._apply_provider(initial.provider, initial.api_key, initial.base_url, initial.model)

    def _set_provider(self, provider_id: str) -> None:
        pid = get_provider(provider_id).provider_id
        idx = self._provider_index.get(pid, self._provider_index.get("custom", 0))
        self.provider.setCurrentIndex(idx)

    def _toggle_api_key_visible(self) -> None:
        if self.api_key.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key.setEchoMode(QLineEdit.EchoMode.Normal)
            self.api_key_btn.setText("隐藏")
        else:
            self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
            self.api_key_btn.setText("显示")

    def _on_provider_changed(self) -> None:
        current = self.provider.currentData()
        if not isinstance(current, str):
            return

        prev_provider = getattr(self, "_current_provider", "")
        if prev_provider:
            self._draft[prev_provider] = (
                self.api_key.text().strip(),
                self.base_url.text().strip(),
                self.model.currentText().strip(),
            )

        api_key, base_url, model = self._load_provider_from_store(current)
        self._apply_provider(current, api_key, base_url, model)

    def _load_provider_from_store(self, provider_id: str) -> tuple[str, str, str]:
        pid = get_provider(provider_id).provider_id
        if pid in self._draft:
            return self._draft[pid]

        store = settings_store()
        spec = get_provider(pid)
        api_key = str(store.value(f"{pid}/api_key", "", type=str))
        base_url = str(store.value(f"{pid}/base_url", spec.default_base_url, type=str)).strip() or spec.default_base_url
        model_default = (spec.default_models[0] if spec.default_models else "").strip()
        model = str(store.value(f"{pid}/model", model_default, type=str)).strip() or model_default
        return (api_key, base_url, model)

    def _apply_provider(self, provider_id: str, api_key: str, base_url: str, model: str) -> None:
        spec = get_provider(provider_id)
        self._current_provider = spec.provider_id

        self.base_url.setPlaceholderText(spec.default_base_url or "https://...")

        self.model.blockSignals(True)
        try:
            self.model.clear()
            if spec.default_models:
                self.model.addItems(list(spec.default_models))
            if model.strip():
                self.model.setCurrentText(model.strip())
        finally:
            self.model.blockSignals(False)

        self.api_key.setText(api_key)
        self.base_url.setText(base_url)
        self.model.setCurrentText(model)

    def settings(self) -> AppSettings:
        return AppSettings(
            provider=str(self.provider.currentData() or "deepseek"),
            api_key=self.api_key.text().strip(),
            base_url=self.base_url.text().strip(),
            model=self.model.currentText().strip(),
        )
