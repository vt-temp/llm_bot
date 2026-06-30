import httpx
import pytest
import respx

from app.services.openrouter_client import call_openrouter


@pytest.mark.asyncio
async def test_call_openrouter_returns_message_content() -> None:
    with respx.mock(assert_all_called=True) as router:
        route = router.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": "Тестовый ответ",
                            }
                        }
                    ]
                },
            )
        )

        result = await call_openrouter("Тестовый запрос")

    assert route.called is True
    assert result == "Тестовый ответ"