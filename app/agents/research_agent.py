import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from app.agents.research_analyst import ResearchAnalystDecision
from app.agents.research_analyst import research_analyst_agent

_RESEARCH_WITH_SERPER = """You are a research agent focused on social media trends, audience
behavior, and platform dynamics.

Use your tools deliberately:
- Serper (search): discover trending topics, news, competitor moves, and cited sources.
- Fetch: pull readable text from URLs you already have.
- Playwright: use when pages need a real browser (heavy JS, dynamic feeds, etc.).

Produce a clear research report each run: executive summary, key trends with evidence, relevant
platforms and formats, audience signals, risks or controversies, and suggested angles for content.
Cite or name sources where possible. If data is uncertain, say so.

You must never discard earlier findings you are given: integrate new work with prior rounds and
remove redundancy only when merging, not when dropping facts."""

_RESEARCH_NO_SERPER = """You are a research agent focused on social media trends, audience
behavior, and platform dynamics.

Serper web search is not configured (set SERPER_API_KEY to enable it). Use Fetch for URLs you know
or infer from the brief, and Playwright when a page needs a real browser.

Produce a clear research report each run: executive summary, key trends with evidence, relevant
platforms and formats, audience signals, risks or controversies, and suggested angles for content.
Cite or name sources where possible. If data is uncertain, say so.

You must never discard earlier findings you are given: integrate new work with prior rounds and
remove redundancy only when merging, not when dropping facts."""


def _research_instructions(user_message: str, *, serper_enabled: bool) -> str:
    base = _RESEARCH_WITH_SERPER if serper_enabled else _RESEARCH_NO_SERPER
    return f"""{base}

## User research brief
{user_message.strip()}"""


def _research_round_prompt(
    user_message: str,
    accumulated_reports: list[str],
    follow_up: str | None,
    *,
    serper_enabled: bool,
) -> str:
    parts = [_research_instructions(user_message, serper_enabled=serper_enabled)]
    if accumulated_reports:
        merged = "\n\n---\n\n".join(accumulated_reports)
        parts.append(
            "## Accumulated research from previous rounds (preserve and build on this; do not lose facts)\n"
            f"{merged}"
        )
    if follow_up:
        parts.append(
            "## Focus this round (address these gaps or directions)\n"
            f"{follow_up.strip()}"
        )
    return "\n\n".join(parts)


def _analyst_prompt(user_message: str, company_context: str, merged_research: str) -> str:
    cc = company_context.strip() or "(none provided)"
    return f"""Original topic / brief:
{user_message.strip()}

Company context:
{cc}

Accumulated research (all rounds):
{merged_research}
"""


def _serper_mcp_params() -> dict:
    key = os.environ.get("SERPER_API_KEY", "")
    params: dict = {
        "command": "npx",
        "args": ["-y", "mcp-server-serper@latest"],
    }
    if key:
        params["env"] = {"SERPER_API_KEY": key}
    return params


@asynccontextmanager
async def research_agent_session(message: str) -> AsyncIterator[Agent]:
    """Open MCP servers and yield a research Agent. User `message` is woven into instructions."""
    fetch_params: dict = {"command": "uvx", "args": ["mcp-server-fetch"]}
    playwright_params: dict = {"command": "npx", "args": ["-y", "@playwright/mcp@latest"]}
    serper_key = os.environ.get("SERPER_API_KEY", "").strip()
    serper_enabled = bool(serper_key)

    async with (
        MCPServerStdio(params=fetch_params, client_session_timeout_seconds=120) as fetch_server,
        MCPServerStdio(params=playwright_params, client_session_timeout_seconds=120) as pw_server,
    ):
        if serper_enabled:
            serper_params = _serper_mcp_params()
            async with MCPServerStdio(
                params=serper_params, client_session_timeout_seconds=120
            ) as serper_server:
                yield Agent(
                    name="research-agent",
                    instructions=_research_instructions(message, serper_enabled=True),
                    model="gpt-4o-mini",
                    mcp_servers=[serper_server, fetch_server, pw_server],
                )
        else:
            yield Agent(
                name="research-agent",
                instructions=_research_instructions(message, serper_enabled=False),
                model="gpt-4o-mini",
                mcp_servers=[fetch_server, pw_server],
            )


async def run_research_pipeline(
    message: str,
    *,
    company_context: str = "",
    max_rounds: int = 5,
    research_max_turns: int = 25,
    analyst_max_turns: int = 15,
) -> tuple[ResearchAnalystDecision, list[str]]:
    """Run research ↔ analyst loop until approval or max rounds. Returns final decision and reports."""
    accumulated: list[str] = []
    follow_up: str | None = None
    last_decision = ResearchAnalystDecision(
        decision="need_more_research",
        gaps_and_follow_up="Initial research pass.",
        rationale="Starting pipeline.",
    )

    async with research_agent_session(message) as research_agent:
        for round_idx in range(max_rounds):
            research_input = _research_round_prompt(
                message,
                accumulated,
                follow_up,
                serper_enabled=bool(os.environ.get("SERPER_API_KEY", "").strip()),
            )
            research_result = await Runner.run(
                research_agent,
                research_input,
                max_turns=research_max_turns,
            )
            report = str(research_result.final_output).strip()
            accumulated.append(f"### Round {round_idx + 1}\n{report}")

            merged = "\n\n---\n\n".join(accumulated)
            analyst_input = _analyst_prompt(message, company_context, merged)
            analyst_result = await Runner.run(
                research_analyst_agent,
                analyst_input,
                max_turns=analyst_max_turns,
            )
            last_decision = analyst_result.final_output
            if not isinstance(last_decision, ResearchAnalystDecision):
                raise TypeError("Analyst must return ResearchAnalystDecision")
            if last_decision.decision == "approved":
                return last_decision, accumulated
            follow_up = last_decision.gaps_and_follow_up.strip() or "Broaden and deepen the prior research; resolve contradictions and add platform-specific detail."

    return last_decision, accumulated