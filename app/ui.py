import gradio as gr
from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from app.agents.assistant_agent import assistant_agent


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
        result = await Runner.run(assistant_agent, messages)
        return str(result.final_output)
    except InputGuardrailTripwireTriggered:
        return "Sorry, I can only help with social media content creation and calendar management."


def build_app():
    demo = gr.ChatInterface(
        fn=chat,
        title="Social Media Manager",
        description="I'll help you create social media content. Tell me what you need!",
    )
    return demo