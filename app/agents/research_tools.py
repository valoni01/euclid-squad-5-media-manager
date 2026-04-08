import json
import os
import re
from typing import Literal
from urllib.parse import urlparse

import httpx
from agents import RunContextWrapper, WebSearchTool, function_tool
from agents.agent import AgentBase
from agents.tool import Tool

_SERPER_SEARCH_URL = "https://google.serper.dev/search"
_DEFAULT_UA = (
    "Mozilla/5.0 (compatible; ResearchAgent/1.0; +https://example.invalid; like SocialMediaManager)"
)
_MAX_FETCH_BYTES = 2_000_000


def _serper_enabled(_ctx: RunContextWrapper, _agent: AgentBase) -> bool:
    return bool(os.environ.get("SERPER_API_KEY", "").strip())


def _html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<!--.*?-->", " ", html)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


@function_tool(is_enabled=_serper_enabled)
async def serper_web_search(
    query: str,
    num_results: int = 10,
) -> str:
    """Search the public web via Serper (Google). Use for trends, news, competitors, and sources."""
    key = os.environ.get("SERPER_API_KEY", "").strip()
    if not key:
        return "Serper is not configured (missing SERPER_API_KEY)."
    n = max(1, min(int(num_results), 20))
    payload = {"q": query.strip(), "num": n}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            _SERPER_SEARCH_URL,
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            content=json.dumps(payload),
        )
        r.raise_for_status()
        data = r.json()
    lines: list[str] = []
    if answer_box := data.get("answerBox"):
        lines.append(f"Answer box: {json.dumps(answer_box, ensure_ascii=False)[:2000]}")
    for item in data.get("organic", [])[:n]:
        title = item.get("title", "")
        link = item.get("link", "")
        snippet = item.get("snippet", "")
        lines.append(f"- {title}\n  {link}\n  {snippet}")
    if not lines:
        return json.dumps(data, ensure_ascii=False)[:12000]
    return "\n".join(lines)


@function_tool
async def fetch_url_text(url: str, max_chars: int = 48_000) -> str:
    """Fetch a URL over HTTP and return extracted plain text. Use for static or server-rendered pages."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "Invalid URL; use http or https with a host."
    cap = max(1000, min(int(max_chars), 200_000))
    headers = {"User-Agent": _DEFAULT_UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(45.0),
        follow_redirects=True,
        headers=headers,
    ) as client:
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            encoding = r.encoding or "utf-8"
            ctype = r.headers.get("content-type", "").lower()
            chunks: list[bytes] = []
            total = 0
            async for chunk in r.aiter_bytes():
                if not chunk:
                    continue
                total += len(chunk)
                if total > _MAX_FETCH_BYTES:
                    return (
                        f"Response too large (>{_MAX_FETCH_BYTES} bytes). "
                        "Try a smaller page, web_search for excerpts, or browser fetch if enabled."
                    )
                chunks.append(chunk)
    raw = b"".join(chunks)
    text = raw.decode(encoding, errors="replace")
    if "html" in ctype or text.lstrip().lower().startswith("<!doctype html") or "<html" in text[:500].lower():
        plain = _html_to_text(text)
    else:
        plain = text
    if len(plain) > cap:
        plain = plain[:cap] + "\n…[truncated]"
    return plain


@function_tool
async def browse_url_with_playwright(
    url: str,
    wait_until: Literal["load", "domcontentloaded", "networkidle", "commit"] = "domcontentloaded",
    max_chars: int = 80_000,
) -> str:
    """Open a URL in a headless Chromium browser and return visible page text. Use for heavy JS or dynamic feeds."""
    from playwright.async_api import async_playwright

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "Invalid URL; use http or https with a host."
    cap = max(1000, min(int(max_chars), 200_000))
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(user_agent=_DEFAULT_UA)
                await page.goto(url, wait_until=wait_until, timeout=90_000)
                body = await page.inner_text("body", timeout=30_000)
            finally:
                await browser.close()
    except Exception as e:
        return (
            f"Playwright error: {e}. If browsers are missing, run: "
            "`uv run playwright install chromium` from the project root."
        )
    text = body.strip()
    if len(text) > cap:
        text = text[:cap] + "\n…[truncated]"
    return text


def build_research_tools(*, include_playwright: bool) -> list[Tool]:
    """Assemble research tools: Serper search XOR OpenAI WebSearchTool, fetch, optional Playwright."""
    tools: list[Tool] = [fetch_url_text]
    if os.environ.get("SERPER_API_KEY", "").strip():
        tools.append(serper_web_search)
    else:
        tools.append(WebSearchTool())
    if include_playwright:
        tools.append(browse_url_with_playwright)
    return tools
