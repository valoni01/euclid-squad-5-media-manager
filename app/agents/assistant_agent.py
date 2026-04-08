from agents import (
    Agent,
    GuardrailFunctionOutput,
    ModelSettings,
    Runner,
    function_tool,
    input_guardrail,
)

from app.agents.guardrails import relevance_checker_agent
from app.agents.Instructions import assistant_agent_instructions


@input_guardrail
async def relevance_guardrail(ctx, agent, input) -> GuardrailFunctionOutput:
    result = await Runner.run(
        relevance_checker_agent,
        input,
        context=ctx.context,
    )
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_relevant,
    )


_last_research_brief: str | None = None


def get_and_clear_research_brief() -> str | None:
    global _last_research_brief
    brief = _last_research_brief
    _last_research_brief = None
    return brief


@function_tool
def submit_request(research_brief: str) -> str:
    """Submit the collected content request once all required details have been confirmed by the user.

    research_brief: A detailed research brief you compose based on the full conversation.
    It should capture the brand context, goals, audience insights, platform nuances,
    trends to explore, and any angles worth investigating — written as a directive for
    a research agent that will gather information to support content creation.
    """
    global _last_research_brief
    _last_research_brief = research_brief.strip()
    return "Research brief submitted successfully. The research team will begin investigating."


assistant_agent = Agent(
    name="assistant-agent",
    instructions=assistant_agent_instructions,
    model="gpt-4o-mini",
    tools=[submit_request],
    input_guardrails=[relevance_guardrail],
    model_settings=ModelSettings(temperature=0.0, max_tokens=1024),
)


