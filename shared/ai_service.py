"""
Storyworks AI 服务封装
"""
import httpx
from typing import Optional, AsyncGenerator
from .config import config


class AIService:
    """AI 服务客户端"""

    @property
    def _config(self):
        return config.ai_config

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """同步生成"""
        ai_config = self._config
        if not ai_config.get("apiKey"):
            raise ValueError("未配置 AI API Key")
        headers = {
            "Authorization": f"Bearer {ai_config['apiKey']}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": ai_config["model"],
            "messages": messages,
            "temperature": temperature if temperature is not None else ai_config.get("temperature", 0.7),
            "max_tokens": max_tokens or ai_config.get("max_tokens", 4096),
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                chat_completions_url(ai_config.get("baseUrl", "")),
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成"""
        ai_config = self._config
        if not ai_config.get("apiKey"):
            raise ValueError("未配置 AI API Key")
        headers = {
            "Authorization": f"Bearer {ai_config['apiKey']}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": ai_config["model"],
            "messages": messages,
            "temperature": temperature if temperature is not None else ai_config.get("temperature", 0.7),
            "max_tokens": max_tokens or ai_config.get("max_tokens", 4096),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                chat_completions_url(ai_config.get("baseUrl", "")),
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        line = line[6:]
                        if line.strip() == "[DONE]":
                            break
                        import json

                        try:
                            data = json.loads(line)
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue


# 单例
ai_service = AIService()


def chat_completions_url(base_url: str) -> str:
    cleaned = str(base_url or "").rstrip("/")
    if cleaned.endswith("/chat/completions"):
        return cleaned
    return f"{cleaned}/chat/completions"
