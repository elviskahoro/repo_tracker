from __future__ import annotations

from hackathon.helper_perplexity import (
    DEFAULT_PROMPT,
    ChatCompletion,
    ChatResponse,
    Client,
    Message,
)
from hackathon.otel import tracer


async def perplexity_get_repo(
    repo_url: str,
    client: Client | None,
) -> str | None:
    with tracer.start_as_current_span("perplexity_get_repo") as span:
        span.add_event(
            name="perplexity_get_repo-started",
            attributes={
                "repo_url": repo_url,
            },
        )
        if client is None:
            error_message: str = "Client is required"
            span.record_exception(AssertionError(error_message))
            span.add_event(
                name="perplexity_get_repo-error",
            )
            raise AssertionError(error_message)

        content: str = DEFAULT_PROMPT.replace(
            "<link_to_github_repository>",
            repo_url,
        )
        chat_completion: ChatCompletion = ChatCompletion(
            messages=[
            Message(
                content=content,
            ),
        ],
    )
    chat_response: ChatResponse = await client.call_perplexity_api(
        chat_completion=chat_completion,
    )
    return chat_response.get_content()
