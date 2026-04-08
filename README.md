# Social Media Manager

## Why We Built This

Creating consistent, high-quality social media content is time-consuming. Teams spend hours researching trends, planning calendars, and writing posts across multiple platforms. We built this AI-powered assistant to automate that entire workflow — from intake to research to a publish-ready content calendar — so teams can focus on strategy instead of execution.

## What It Does

An end-to-end multi-agent system that turns a simple content request into a researched, structured media plan:

- **Conversational Intake** — A chat assistant gathers brand context, goals, audience, platforms, tone, and topics through natural conversation (not a long form).
- **Input Guardrails** — A relevance checker ensures conversations stay on-topic (social media content creation only) and rejects off-topic requests.
- **Automated Research Pipeline** — A research agent investigates trends, audience behaviour, and platform dynamics using web search and URL fetching, running multiple rounds until an analyst agent approves the coverage.
- **Research Analyst Review** — An analyst agent evaluates each research round, identifies gaps, and either requests deeper investigation or approves the findings with actionable content guidance.
- **Media Planner** — Once research is approved, a planner agent produces a full content calendar with concrete posts: hooks, captions, hashtags, platform/format assignments, posting windows, and media briefs.
- **Plan Persistence** — Every approved media plan is saved as structured JSON to `data/plans/`, creating a searchable history of campaigns.
- **Plan Retrieval** — The assistant can list and display previously saved media plans on demand, so users can review past calendars without leaving the chat.
- **Text-to-Speech** — Optional TTS powered by OpenAI's audio API lets the assistant read responses aloud (toggle on/off in the UI).
- **Gradio Chat UI** — A web-based chat interface that ties everything together with markdown-rendered responses.

## Architecture

```
User (Gradio Chat UI)
  └─ Assistant Agent (intake + routing)
       ├─ [guardrail] Relevance Checker
       ├─ [tool] submit_request → Research Pipeline
       │    ├─ Research Agent (web search, URL fetch)
       │    └─ Research Analyst (approve / request more)
       ├─ [on approval] Media Planner → Plan Saver (JSON to disk)
       ├─ [tool] list_saved_plans
       └─ [tool] get_plan_details
```

## Tech Stack

- **Python 3.12+**
- **OpenAI Agents SDK** (`openai-agents`) — multi-agent orchestration, function tools, guardrails, structured outputs
- **OpenAI API** — GPT-4o-mini for all agents, TTS-1 for text-to-speech
- **Gradio** — chat UI
- **Pydantic** — structured schemas for media plans
- **Playwright** (optional) — headless browser for JS-heavy pages during research

## Getting Started

1. Install [uv](https://docs.astral.sh/uv/) and sync dependencies:
   ```
   uv sync
   ```

2. Copy `example.env` to `.env` and fill in your keys:
   ```
   cp example.env .env
   ```
   Required: `OPENAI_API_KEY`
   Optional: `SERPER_API_KEY` (if unset, research uses OpenAI's built-in web search)

3. Launch the app:
   ```
   uv run python main.py
   ```
   Open the Gradio URL printed in the terminal.

## Project Structure

```
main.py                          # Entry point — loads env, launches Gradio
app/
  ui.py                          # Gradio chat interface + orchestration
  tts.py                         # OpenAI TTS utility
  agents/
    Instructions.py              # Assistant agent system prompt
    assistant_agent.py           # Main assistant (intake, routing, tools)
    guardrails.py                # Relevance checker guardrail
    research_agent.py            # Multi-round research pipeline
    research_analyst.py          # Analyst agent (approve/reject research)
    research_tools.py            # Web search + URL fetch tools
    Mediaplanner/
      media_planner.py           # Media planner agent + runner
      social_plan_schema.py      # Pydantic schemas (MediaPlan, PlannedPost)
      plan_saver.py              # Save, load, list, and format plans
  data/
    plans/                       # Saved media plan JSON files
```

## Environment Variables

Add any new variable names to `example.env` so all contributors can set them up locally.

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key for agents and TTS |
| `SERPER_API_KEY` | No | Google search via [Serper](https://serper.dev); falls back to OpenAI web search |
