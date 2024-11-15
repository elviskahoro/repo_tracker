from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from pydantic.dataclasses import dataclass

from hackathon.otel import tracer

if TYPE_CHECKING:
    from httpx import Response

    from .model_chat_completion import ChatCompletion

from .model_chat_response import ChatResponse

BASE_API_URL: str = "https://api.perplexity.ai"
TIMEOUT: int = 30
SPAN_KEY: str = "perplexity"


@dataclass
class Client:
    token: str

    @classmethod
    def set_up_client_from_tokens(
        cls: type[Client],
        tokens: dict[str, str | None],
    ) -> Client | None:
        span_name: str = f"{SPAN_KEY}-client-set_up_client_from_tokens"
        with tracer.start_as_current_span(span_name) as span:
            token: str | None = tokens.get("PERPLEXITY_API_KEY")
            if token is None:
                span.add_event(
                    name="missing_tokens-perplexity",
                    attributes={
                        "missing_token": "PERPLEXITY_API_KEY",
                    },
                )
                return None

        return cls(
            token=token,
        )

    async def call_perplexity_api(
        self: Client,
        chat_completion: ChatCompletion,
    ) -> ChatResponse:
        span_name: str = f"{SPAN_KEY}-client-call_perplexity_api"
        with tracer.start_as_current_span(span_name) as span:
            api_key = self.token
            headers: dict[str, str] = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            try:
                async with httpx.AsyncClient(
                    timeout=TIMEOUT,
                ) as client:
                    response: Response = await client.post(
                        url=f"{BASE_API_URL}/chat/completions",
                        headers=headers,
                        content=chat_completion.model_dump_json(),
                    )
                    response.raise_for_status()

            except httpx.ReadTimeout as e:
                span.record_exception(e)
                error_message: str = "Perplexity API request timed out"
                span.add_event(
                    name="perplexity_api_request_timed_out",
                    attributes={
                        "exception": str(e),
                        "error_message": error_message,
                    },
                )
                raise TimeoutError(error_message) from e

            return ChatResponse.model_validate(
                obj=response.json(),
            )

def set_up_client_from_tokens(
    tokens: dict[str, str | None],
) -> Client | None:
    span_name: str = f"{SPAN_KEY}-set_up_client_from_tokens"
    with tracer.start_as_current_span(span_name):
        return Client.set_up_client_from_tokens(
            tokens=tokens,
        )
