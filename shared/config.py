"""
Storyworks 共享配置管理
"""
import json
import os
from pathlib import Path
from typing import Optional


class Config:
    """全局配置管理器"""

    _instance: Optional["Config"] = None
    _config: dict = {}
    _config_mtime_ns: Optional[int] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """加载配置文件"""
        # shared/config.py -> Storyworks/
        base_dir = Path(__file__).parent.parent
        env_config_path = os.getenv("STORYWORKS_CONFIG_PATH")
        if env_config_path:
            config_paths = [Path(env_config_path)]
        else:
            config_paths = [
                base_dir / "config.json",
                Path.cwd() / "config.json",
            ]
        self._config_path = config_paths[0]
        self._config_mtime_ns = None

        for config_path in config_paths:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                self._config_path = config_path
                self._config_mtime_ns = self._file_mtime_ns(config_path)
                self._apply_env_overrides()
                return

        # 默认配置
        self._config = {
            "ai": {
                "provider": "openai_compatible",
                "baseUrl": "https://opencode.ai/zen/go/v1",
                "apiKey": "",
                "model": "deepseek-v4-pro",
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            "projects_dir": "./projects",
        }
        self._apply_env_overrides()

    def _file_mtime_ns(self, path: Path) -> Optional[int]:
        try:
            return path.stat().st_mtime_ns
        except OSError:
            return None

    def _maybe_reload_config(self):
        """Reload config.json if another Storyworks backend saved it."""
        config_path = getattr(self, "_config_path", None)
        if not config_path:
            return
        config_path = Path(config_path)
        mtime_ns = self._file_mtime_ns(config_path)
        if mtime_ns is None or mtime_ns == getattr(self, "_config_mtime_ns", None):
            return
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except (OSError, json.JSONDecodeError):
            return
        self._config_mtime_ns = mtime_ns
        self._apply_env_overrides()

    def save(self):
        """保存当前配置到配置文件。"""
        config_path = getattr(self, "_config_path", self.base_dir / "config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)
        self._config_mtime_ns = self._file_mtime_ns(config_path)

    def public_ai_config(self) -> dict:
        """返回可展示的 AI 配置，不泄露 API Key 明文。"""
        ai_config = dict(self.ai_config)
        has_api_key = bool(ai_config.get("apiKey"))
        ai_config["apiKey"] = ""
        ai_config["has_api_key"] = has_api_key
        ai_config["config_path"] = str(getattr(self, "_config_path", self.base_dir / "config.json"))
        return ai_config

    def update_ai_config(self, values: dict) -> dict:
        """更新并保存 AI 配置。空 API Key 默认保留原值。"""
        self._maybe_reload_config()
        ai_config = self._config.setdefault("ai", {})
        provider = str(values.get("provider") or ai_config.get("provider") or "openai_compatible").strip()
        if provider not in {"openai_compatible", "mock"}:
            raise ValueError("不支持的 AI Provider")

        ai_config["provider"] = provider
        aliases = {
            "baseUrl": ["baseUrl", "base_url", "baseURL"],
            "model": ["model"],
        }
        for target_key, source_keys in aliases.items():
            for source_key in source_keys:
                if source_key in values:
                    ai_config[target_key] = str(values.get(source_key) or "").strip()
                    break

        if values.get("clearApiKey"):
            ai_config["apiKey"] = ""
        else:
            api_key = values.get("apiKey", values.get("api_key"))
            if str(api_key or "").strip():
                ai_config["apiKey"] = str(api_key).strip()

        if "temperature" in values:
            try:
                ai_config["temperature"] = float(values.get("temperature"))
            except (TypeError, ValueError) as exc:
                raise ValueError("temperature 必须是数字") from exc
        max_tokens_value = values.get("max_tokens", values.get("maxTokens"))
        if max_tokens_value is not None:
            try:
                max_tokens = int(max_tokens_value)
            except (TypeError, ValueError) as exc:
                raise ValueError("max_tokens 必须是整数") from exc
            if max_tokens <= 0:
                raise ValueError("max_tokens 必须大于 0")
            ai_config["max_tokens"] = max_tokens

        self.save()
        self._apply_env_overrides()
        return self.public_ai_config()

    def _apply_env_overrides(self):
        """Allow local secrets and deployment config to override config.json."""
        ai_config = self._config.setdefault("ai", {})
        env_map = {
            "STORYWORKS_AI_PROVIDER": "provider",
            "STORYWORKS_AI_BASE_URL": "baseUrl",
            "STORYWORKS_AI_API_KEY": "apiKey",
            "STORYWORKS_AI_MODEL": "model",
        }
        for env_name, key in env_map.items():
            value = os.getenv(env_name)
            if value:
                ai_config[key] = value
        temperature = os.getenv("STORYWORKS_AI_TEMPERATURE")
        if temperature:
            try:
                ai_config["temperature"] = float(temperature)
            except ValueError:
                pass
        max_tokens = os.getenv("STORYWORKS_AI_MAX_TOKENS")
        if max_tokens:
            try:
                ai_config["max_tokens"] = int(max_tokens)
            except ValueError:
                pass
        projects_dir = os.getenv("STORYWORKS_PROJECTS_DIR")
        if projects_dir:
            self._config["projects_dir"] = projects_dir

    @property
    def ai_config(self) -> dict:
        self._maybe_reload_config()
        return self._config.get("ai", {})

    @property
    def projects_dir(self) -> str:
        self._maybe_reload_config()
        return self._config.get("projects_dir", "./projects")

    @property
    def base_dir(self) -> Path:
        """获取项目根目录"""
        return Path(__file__).parent.parent


# 单例
config = Config()
