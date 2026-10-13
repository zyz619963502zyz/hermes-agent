"""Keep gateway-owned display decoration separate from speech payloads."""

from __future__ import annotations

import logging
from typing import Any

from agent.i18n import t
from gateway.config import Platform

logger = logging.getLogger("gateway.run")


_REASONING_QUOTE_STYLES = {
    "subtext": ("gateway.reasoning.quote_label_discord", "-# ", "-#"),
    "blockquote": ("gateway.reasoning.quote_label_md", "> ", ">"),
}


def render_reasoning_for_delivery(
    agent_result: dict[str, Any],
    response: str,
    source: Any,
    intentional_silence: bool,
    *,
    show_reasoning_default: bool,
) -> tuple[str, str | None]:
    """Return localized display text plus the undecorated answer to speak, when needed."""
    from gateway.run import _load_gateway_config, _platform_config_key, _resolve_gateway_display_bool

    try:
        show_reasoning = _resolve_gateway_display_bool(
            _load_gateway_config(), _platform_config_key(source.platform), "show_reasoning",
            default=show_reasoning_default, platform=source.platform,
            require_platform_override_for={Platform.MATTERMOST},
        )
    except Exception:
        logger.debug("reasoning display policy resolution failed", exc_info=True)
        show_reasoning = False if source.platform == Platform.MATTERMOST else show_reasoning_default
    last_reasoning = agent_result.get("last_reasoning")
    if not (show_reasoning and response and not intentional_silence and last_reasoning):
        return response, None

    lines = last_reasoning.strip().splitlines()
    display_reasoning = (
        "\n".join(lines[:15]) + t("gateway.reasoning.more_lines", count=len(lines) - 15)
        if len(lines) > 15 else last_reasoning.strip()
    )
    try:
        from gateway.display_config import resolve_display_setting
        reasoning_style = resolve_display_setting(
            _load_gateway_config(), _platform_config_key(source.platform), "reasoning_style", "code",
        )
    except Exception:
        logger.debug("reasoning display style resolution failed", exc_info=True)
        reasoning_style = "code"
    quote = _REASONING_QUOTE_STYLES.get(reasoning_style)
    if quote:
        header_key, prefix, empty = quote
        quoted = "\n".join(f"{prefix}{line}" if line else empty for line in display_reasoning.splitlines())
        return f"{t(header_key)}\n{quoted}\n\n{response}", response

    from gateway.stream_consumer_fences import escape_code_fences_for_display
    escaped_reasoning = escape_code_fences_for_display(display_reasoning)
    return t("gateway.reasoning.block", reasoning=escaped_reasoning, response=response), response


def carry_spoken_response_suffix(
    spoken_response: str | None,
    response_before: str | None,
    response_after: str | None,
) -> str | None:
    """Carry gateway-owned post-processing into an explicit spoken payload."""
    if spoken_response is None or response_after == response_before:
        return spoken_response
    before = str(response_before or "")
    after = str(response_after or "")
    if after.startswith(before):
        return f"{spoken_response}{after[len(before):]}"
    trimmed_before = before.rstrip()
    if trimmed_before and after.startswith(trimmed_before):
        return f"{str(spoken_response).rstrip()}{after[len(trimmed_before):]}"
    # Never fall back to the visible payload: it may contain private reasoning.
    return spoken_response
