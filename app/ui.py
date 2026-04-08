import gradio as gr
from agents import Runner, trace
from agents.exceptions import InputGuardrailTripwireTriggered
from app.agents.assistant_agent import assistant_agent, get_and_clear_research_brief
from app.agents.research_agent import run_research_pipeline
from app.agents.Mediaplanner.media_planner import run_media_planner


def _extract_text(content) -> str:
    """Ensure content is a plain string regardless of Gradio's format."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            item.get("text", "") or item.get("value", "") or str(item)
            for item in content
            if isinstance(item, dict)
        )
    return str(content)


async def chat(message, history):
    messages = []
    for entry in history:
        if isinstance(entry, dict):
            messages.append({"role": entry["role"], "content": _extract_text(entry["content"])})
        elif isinstance(entry, (list, tuple)) and len(entry) == 2:
            messages.append({"role": "user", "content": _extract_text(entry[0])})
            if entry[1]:
                messages.append({"role": "assistant", "content": _extract_text(entry[1])})
    messages.append({"role": "user", "content": _extract_text(message)})

    try:
        with trace("Social Media Manager"):
            result = await Runner.run(assistant_agent, messages)
            assistant_response = str(result.final_output)

            research_brief = get_and_clear_research_brief()
            if research_brief:
                decision, reports = await run_research_pipeline(research_brief)
                research_output = "\n\n---\n\n".join(reports)

                if decision.decision == "approved":
                    plan, plan_summary = await run_media_planner(
                        user_message=research_brief,
                        company_context="",
                        horizon_label="2 weeks",
                        analyst_decision=decision,
                        merged_research=research_output,
                    )
                    return (
                        f"{assistant_response}\n\n"
                        f"**Research Results ({decision.decision}):**\n\n"
                        f"{research_output}\n\n"
                        f"---\n\n"
                        f"**Media Plan: {plan.plan_title}**\n\n"
                        f"{plan_summary}"
                    )

                return (
                    f"{assistant_response}\n\n"
                    f"**Research Results ({decision.decision}):**\n\n"
                    f"{research_output}"
                )

            return assistant_response
    except InputGuardrailTripwireTriggered:
        return "Sorry, I can only help with social media content creation and calendar management."


def build_app():
    demo = gr.ChatInterface(
        fn=chat,
        title="Social Media Manager",
        description="I'll help you create social media content. Tell me what you need!",
    )
    return demo