"""URL redaction helpers for safe logging.

IPTV playlist and stream URLs frequently embed credentials -- as userinfo
(``http://user:pass@host``), as query parameters (Xtream Codes:
``?username=...&password=...``) or even as path segments
(``/<username>/<password>/...``). Logging such URLs verbatim leaks those
secrets into log files and the console.

:func:`redact_url` keeps only the part that is safe and useful for debugging
(scheme + host + port) and drops everything that can carry a secret
(userinfo, path, query, fragment).
"""
from urllib.parse import urlsplit


def redact_url(url: str) -> str:
    """
    Return a log-safe version of ``url`` with any credentials stripped.

    Keeps only ``scheme://host[:port]`` and appends ``/...`` to signal that a
    path/query was removed. Non-HTTP sources (local file paths or inline M3U
    content) are reported generically so their contents never reach the log.

    Args:
        url: The URL (or local path / inline content) about to be logged.

    Returns:
        A string that is safe to write to logs.
    """
    if not url:
        return "<empty>"
    try:
        parts = urlsplit(url)
    except Exception:
        return "<unparseable-url>"

    if parts.scheme in ("http", "https") and parts.hostname:
        port = f":{parts.port}" if parts.port else ""
        return f"{parts.scheme}://{parts.hostname}{port}/..."

    # Local file path or inline M3U content -- never echo it.
    return "<local-source>"
