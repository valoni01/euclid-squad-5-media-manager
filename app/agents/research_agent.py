import os

from agents import Agent, Runner

from app.agents.research_analyst import ResearchAnalystDecision
from app.agents.research_analyst import research_analyst_agent
from app.agents.research_tools import build_research_tools

RESEARCH_PLAYWRIGHT_ENABLED = False


def _research_instructions(
    user_message: str,
    *,
    serper_enabled: bool,
    playwright_enabled: bool,
) -> str:
    if serper_enabled:
        search_bullet = (
            "- serper_web_search: discover trending topics, news, competitor moves, and cited sources."
        )
    else:
        search_bullet = (
            "- web_search (OpenAI hosted tool): discover trending topics, news, competitors, "
            "and sources. Serper is not configured; this replaces serper_web_search."
        )

    fetch_bullet = (
        "- fetch_url_text: pull plain text from URLs for static or server-rendered pages."
    )

    if playwright_enabled:
        pw_bullet = (
            "- browse_url_with_playwright: use when pages need a real browser "
            "(heavy JS, dynamic feeds, etc.)."
        )
    else:
        pw_bullet = (
            "- Headless browser is disabled on this deployment. Rely on web search and "
            "fetch_url_text; for heavy JS pages, find summaries or mirrors via search."
        )

    base = f"""You are a research agent focused on social media trends, audience
behavior, and platform dynamics.

Use your tools deliberately:
{search_bullet}
{fetch_bullet}
{pw_bullet}

Produce a clear research report each run: executive summary, key trends with evidence, relevant
platforms and formats, audience signals, risks or controversies, and suggested angles for content.
Cite or name sources where possible. If data is uncertain, say so.

You must never discard earlier findings you are given: integrate new work with prior rounds and
remove redundancy only when merging, not when dropping facts."""

    return f"""{base}

## User research brief
{user_message.strip()}"""


def _research_round_prompt(
    user_message: str,
    accumulated_reports: list[str],
    follow_up: str | None,
    *,
    serper_enabled: bool,
    playwright_enabled: bool,
) -> str:
    parts = [
        _research_instructions(
            user_message,
            serper_enabled=serper_enabled,
            playwright_enabled=playwright_enabled,
        )
    ]
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


def build_research_agent(message: str) -> Agent:
    """Build the research Agent with local tools and either Serper or OpenAI WebSearchTool."""
    serper_key = os.environ.get("SERPER_API_KEY", "").strip()
    serper_enabled = bool(serper_key)
    tools = build_research_tools(include_playwright=RESEARCH_PLAYWRIGHT_ENABLED)
    return Agent(
        name="research-agent",
        instructions=_research_instructions(
            message,
            serper_enabled=serper_enabled,
            playwright_enabled=RESEARCH_PLAYWRIGHT_ENABLED,
        ),
        model="gpt-4o-mini",
        tools=tools,
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

    serper_enabled = bool(os.environ.get("SERPER_API_KEY", "").strip())
    research_agent = build_research_agent(message)
    for round_idx in range(max_rounds):
        research_input = _research_round_prompt(
            message,
            accumulated,
            follow_up,
            serper_enabled=serper_enabled,
            playwright_enabled=RESEARCH_PLAYWRIGHT_ENABLED,
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
