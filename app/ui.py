import gradio as gr
from app.agents.sample_agent import run_agent

def chat(message, history):
    response = run_agent(message, history)
    return response

def build_app():
    demo = gr.ChatInterface(
        fn=chat,
        title="My Agent",
        description="Interact with the agent locally"
    )
    return demo