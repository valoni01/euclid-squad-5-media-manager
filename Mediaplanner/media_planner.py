"""Media planner agent: turns approved analyst guidance into a dated calendar + saves locally."""

from __future__ import annotations

from agents import Agent, Runner
from agents.items import ItemHelpers, MessageOutputItem, ToolCallOutputItem

from app.agents.plan_saver import persist_media_plan, save_media_plan
from app.agents.research_analyst import ResearchAnalystDecision
from app.agents.social_plan_schema import MediaPlan


def _media_planner_instructions() -> str:
    return """You are a social media planner for an early-stage company.

You receive:
- The user's original objective or campaign brief.
- Company context (products, audience, markets, tone, constraints).
- Planning horizon (e.g. number of weeks or days).
- Approved research analyst guidance (pillars, tone, cadence, platforms).
- Condensed research background (trends, risks, proof points).

Your job:
1. Stay within the company's scope and brand—no unrelated verticals or off-brand stunts.
2. Design a practical calendar: concrete posts across the horizon with varied formats.
3. Each post must include hook, caption body, platform, format, optional hashtags, and a brief for the media (photo/video) agent.
4. Add compliance / risk notes where claims, contests, or regulated topics might apply.
5. Finish with metrics_to_watch and handoff_notes_for_social_manager.

When the structured MediaPlan is ready, call save_media_plan exactly once:
- plan_json: JSON serialization of your MediaPlan (must validate against the MediaPlan schema).
- filename_slug: short kebab-case slug from plan_title (e.g. "april-launch-campaign").

After the tool returns, echo the tool message (saved path) in your final natural-language reply."""


def _media_planner_prompt(
    *,
    user_message: str,
    company_context: str,
    horizon_label: str,
    analyst: ResearchAnalystDecision,
    merged_research: str,
) -> str:
    cc = company_context.strip() or "(none provided)"
    guidance = analyst.final_content_guidance.strip() or "(none)"
    return f"""## Original brief
{user_message.strip()}

## Company context
{cc}

## Planning horizon
{horizon_label.strip()}

## Approved analyst guidance (must shape this plan)
{guidance}

## Research background (all rounds, condensed)
{merged_research.strip()[:120_000]}

Produce a complete MediaPlan for the horizon, then call save_media_plan as instructed.
"""


def build_media_planner_agent() -> Agent:
    return Agent(
        name="media-planner",
        instructions=_media_planner_instructions(),
        model="gpt-4o-mini",
        tools=[save_media_plan],
        output_type=MediaPlan,
    )


def _save_ack_from_new_items(new_items: list) -> str | None:
    for item in reversed(new_items):
        if not isinstance(item, ToolCallOutputItem):
            continue
        text = str(item.output)
        if "Saved media plan to" in text:
            return text.strip()
    return None


async def run_media_planner(
    *,
    user_message: str,
    company_context: str,
    horizon_label: str,
    analyst_decision: ResearchAnalystDecision,
    merged_research: str,
    max_turns: int = 35,
) -> tuple[MediaPlan, str]:
    """Run planner; returns structured plan and final assistant text (includes save path when tool ran)."""
    if analyst_decision.decision != "approved":
        raise ValueError("Research analyst must approve before running the media planner.")

    agent = build_media_planner_agent()
    prompt = _media_planner_prompt(
        user_message=user_message,
        company_context=company_context,
        horizon_label=horizon_label,
        analyst=analyst_decision,
        merged_research=merged_research,
    )
    result = await Runner.run(agent, prompt, max_turns=max_turns)
    plan = result.final_output_as(MediaPlan, raise_if_incorrect_type=True)
    ack = _save_ack_from_new_items(result.new_items)
    if ack is None:
        path = persist_media_plan(plan, plan.plan_title)
        ack = f"Saved media plan to {path}"
    text_bits: list[str] = []
    for item in result.new_items:
        if isinstance(item, MessageOutputItem):
            text_bits.append(ItemHelpers.text_message_output(item))
    assistant_summary = "\n".join(text_bits).strip() or ack
    return plan, assistant_summary
