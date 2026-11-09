"""Collect the sources the agents actually used, and keep report links honest.

The writer only sees text, so it can invent URLs. These helpers take the real
URLs from the agents' tool calls, give the writer a numbered list to cite from,
strip any link that is not on that list, and append a Sources section built
from the list itself.
"""

import re
from urllib.parse import urlparse

from langchain_core.messages import AIMessage, ToolMessage

_RESULT_RE = re.compile(r"Title:\s*(.+?)\s*\n\s*URL:\s*(\S+)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_SCRAPE_FAILED = ("Could not", "HTTP error", "Request timed out")


def _key(url: str) -> str:
    return url.strip().rstrip("/").lower()


def collect_sources(messages, sources: list[dict] | None = None) -> list[dict]:
    """Add the URLs found by web_search and read by scrape_url to `sources`.

    Each source is {"title": str, "url": str, "read": bool}; `read` is True when
    the reader agent scraped the page successfully.
    """
    sources = list(sources or [])
    by_url = {_key(s["url"]): s for s in sources}
    scrape_calls = {}

    for msg in messages:
        if isinstance(msg, AIMessage):
            for call in msg.tool_calls:
                if call["name"] == "scrape_url" and "url" in call["args"]:
                    scrape_calls[call["id"]] = call["args"]["url"]
        elif isinstance(msg, ToolMessage):
            if msg.name == "web_search":
                for title, url in _RESULT_RE.findall(msg.text):
                    if _key(url) not in by_url:
                        by_url[_key(url)] = {"title": title, "url": url, "read": False}
                        sources.append(by_url[_key(url)])
            elif msg.name == "scrape_url" and msg.tool_call_id in scrape_calls:
                if msg.text.startswith(_SCRAPE_FAILED):
                    continue
                url = scrape_calls[msg.tool_call_id]
                if _key(url) not in by_url:
                    by_url[_key(url)] = {"title": urlparse(url).netloc, "url": url, "read": False}
                    sources.append(by_url[_key(url)])
                by_url[_key(url)]["read"] = True

    return sources


def format_sources(sources: list[dict]) -> str:
    """Numbered list handed to the writer as the only sources it may cite."""
    if not sources:
        return "No sources were retrieved."
    return "\n".join(
        f"[{i}] {s['title']} — {s['url']}{' (read in full)' if s['read'] else ''}"
        for i, s in enumerate(sources, start=1)
    )


def finalize_report(report: str, sources: list[dict]) -> str:
    """Unlink any URL the agents did not find, then append the Sources section."""
    allowed = {_key(s["url"]) for s in sources}

    def check(match: re.Match) -> str:
        return match.group(0) if _key(match.group(2)) in allowed else match.group(1)

    report = _LINK_RE.sub(check, report).rstrip()
    if not sources:
        return report

    lines = [
        f"{i}. [{s['title']}]({s['url']}){' · read in full' if s['read'] else ''}"
        for i, s in enumerate(sources, start=1)
    ]
    return report + "\n\n## Sources\n\n" + "\n".join(lines) + "\n"
