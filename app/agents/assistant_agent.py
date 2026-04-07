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
from app.agents.models import UserRequest


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


@function_tool
def submit_request(
    content_number: int,
    content_topics: list[str],
    content_tone: str,
    content_audience: str,
    content_platform: str,
    content_trends: list[str] | None = None,
    content_extra_details: str = "",
) -> str:
    """Submit the collected content request once all required details have been confirmed by the user."""
    request = UserRequest(
        content_number=content_number,
        content_topics=content_topics,
        content_tone=content_tone,
        content_audience=content_audience,
        content_platform=content_platform,
        content_trends=content_trends or [],
        content_extra_details=content_extra_details,
    )
    return f"Request submitted successfully: {request.model_dump_json(indent=2)}"


assistant_agent = Agent(
    name="assistant-agent",
    instructions=assistant_agent_instructions,
    model="gpt-4o-mini",
    tools=[submit_request],
    input_guardrails=[relevance_guardrail],
    model_settings=ModelSettings(temperature=0.0),
)


