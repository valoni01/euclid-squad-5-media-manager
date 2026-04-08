from agents import Agent
from typing import Literal
from pydantic import BaseModel, Field

class ResearchAnalystDecision(BaseModel):
    """Structured verdict from the research analyst after each research round."""

    decision: Literal["need_more_research", "approved"] = Field(
        description="need_more_research: run another research round; approved: research is sufficient."
    )
    gaps_and_follow_up: str = Field(
        default="",
        description="When decision is need_more_research: concrete gaps, angles, platforms, metrics, or regions to investigate next.",
    )
    final_content_guidance: str = Field(
        default="",
        description="When decision is approved: actionable content plan (formats, pillars, tone, cadence, platforms) aligned to the company context.",
    )
    rationale: str = Field(
        default="",
        description="Short justification for the decision.",
    )

research_analyst_agent = Agent(
    name="research-analyst",
    instructions="""You are a research analyst for social media and marketing teams.

You receive:
- The original user topic or brief.
- Optional company context (brand, audience, products, markets).
- One or more accumulated research reports from the research agent (all rounds merged).

Your job:
1. Parse and evaluate coverage: platforms, trends, recency, audience fit, risks, and gaps.
2. If information is thin, contradictory, outdated, or missing key angles, set decision to
   "need_more_research" and spell out specific follow-up questions or search directions in
   gaps_and_follow_up. Do not discard prior research; the next round will merge with what exists.
3. When research is solid enough to brief content creators, set decision to "approved" and
   produce final_content_guidance: concrete recommendations on content types, themes, formats,
   tone, posting cadence, and platform priorities tailored to the company context.

Always return structured output matching the schema. Only one of gaps_and_follow_up vs
final_content_guidance should be substantively filled based on decision.""",
    model="gpt-4o-mini",
    output_type=ResearchAnalystDecision,
)
