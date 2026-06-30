from httpx import AsyncClient, HTTPError, HTTPStatusError, TimeoutException

from app.core.config import settings


class OpenRouterError(RuntimeError):
    """Ошибка взаимодействия с API OpenRouter."""

    pass


def _extract_error_details(response) -> str:
    """Извлекает человекочитаемое описание ошибки из ответа OpenRouter."""
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return text[:300] if text else "без описания"

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        message = error.get("message")
        metadata = error.get("metadata")
        raw = metadata.get("raw") if isinstance(metadata, dict) else None
        if message and raw:
            return f"{message}: {raw}"
        if message:
            return str(message)

    return str(payload)[:300]


async def call_openrouter(prompt: str) -> str:
    """Отправляет пользовательский запрос в OpenRouter и возвращает текст ответа модели."""
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": settings.openrouter_site_url,
        "X-Title": settings.openrouter_app_name,
    }
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    try:
        async with AsyncClient(base_url=settings.openrouter_base_url, timeout=60.0) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
    except TimeoutException as exc:
        raise OpenRouterError("Превышено время ожидания ответа OpenRouter") from exc
    except HTTPStatusError as exc:
        details = _extract_error_details(exc.response)
        raise OpenRouterError(
            f"OpenRouter вернул ошибку {exc.response.status_code}: {details}"
        ) from exc
    except HTTPError as exc:
        raise OpenRouterError("Ошибка сети при обращении к OpenRouter") from exc

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("OpenRouter вернул ответ в неожиданном формате") from exc