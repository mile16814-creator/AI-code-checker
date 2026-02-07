from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderSpec:
    provider_id: str
    display_name: str
    default_base_url: str
    default_models: tuple[str, ...]


PROVIDERS: tuple[ProviderSpec, ...] = (
    ProviderSpec(
        provider_id="deepseek",
        display_name="DeepSeek",
        default_base_url="https://api.deepseek.com",
        default_models=("deepseek-chat", "deepseek-reasoner"),
    ),
    ProviderSpec(
        provider_id="openai",
        display_name="OpenAI",
        default_base_url="https://api.openai.com",
        default_models=("gpt-4o-mini", "gpt-4o", "gpt-5.2"),
    ),
    ProviderSpec(
        provider_id="openrouter",
        display_name="OpenRouter",
        default_base_url="https://openrouter.ai/api/v1",
        default_models=("openai/gpt-4o-mini", "openai/gpt-5.2"),
    ),
    ProviderSpec(
        provider_id="groq",
        display_name="Groq",
        default_base_url="https://api.groq.com/openai/v1",
        default_models=("llama-3.3-70b-versatile", "llama3-8b-8192"),
    ),
    ProviderSpec(
        provider_id="together",
        display_name="Together",
        default_base_url="https://api.together.xyz/v1",
        default_models=("openai/gpt-oss-20b", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"),
    ),
    ProviderSpec(
        provider_id="siliconflow",
        display_name="SiliconFlow",
        default_base_url="https://api.siliconflow.cn/v1",
        default_models=("deepseek-ai/DeepSeek-V3.2", "deepseek-ai/DeepSeek-R1", "Qwen/Qwen3-32B"),
    ),
    ProviderSpec(
        provider_id="moonshot",
        display_name="Moonshot（Kimi）",
        default_base_url="https://api.moonshot.cn/v1",
        default_models=("kimi-k2-turbo-preview", "moonshot-v1-8k"),
    ),
    ProviderSpec(
        provider_id="custom",
        display_name="自定义（OpenAI 兼容）",
        default_base_url="",
        default_models=(),
    ),
)


def get_provider(provider_id: str) -> ProviderSpec:
    pid = (provider_id or "").strip().lower()
    for p in PROVIDERS:
        if p.provider_id == pid:
            return p
    return next(p for p in PROVIDERS if p.provider_id == "custom")

