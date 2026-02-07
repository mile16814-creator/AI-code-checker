from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QSettings, QStandardPaths

from app.providers import get_provider


def settings_path() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    if not base:
        base = str(Path.home() / ".config")
    cfg_dir = Path(base) / "deepseek_code_quality_tool"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "settings.ini"


def settings_store() -> QSettings:
    return QSettings(str(settings_path()), QSettings.Format.IniFormat)


@dataclass(frozen=True)
class AppSettings:
    provider: str
    api_key: str
    base_url: str
    model: str


DEFAULT_PROVIDER = "deepseek"


def load_settings() -> AppSettings:
    store = settings_store()
    provider = str(store.value("provider/current", DEFAULT_PROVIDER, type=str)).strip() or DEFAULT_PROVIDER
    spec = get_provider(provider)
    provider = spec.provider_id

    api_key = str(store.value(f"{provider}/api_key", "", type=str))
    base_url_default = spec.default_base_url
    model_default = (spec.default_models[0] if spec.default_models else "").strip()

    base_url = str(store.value(f"{provider}/base_url", base_url_default, type=str)).strip() or base_url_default
    model = str(store.value(f"{provider}/model", model_default, type=str)).strip() or model_default

    return AppSettings(provider=provider, api_key=api_key, base_url=base_url, model=model)


def save_settings(settings: AppSettings) -> None:
    store = settings_store()
    spec = get_provider(settings.provider)
    provider = spec.provider_id
    store.setValue("provider/current", provider)
    store.setValue(f"{provider}/api_key", settings.api_key)
    store.setValue(f"{provider}/base_url", settings.base_url.strip() or spec.default_base_url)
    store.setValue(
        f"{provider}/model",
        settings.model.strip() or (spec.default_models[0] if spec.default_models else ""),
    )
    store.sync()
