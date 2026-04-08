"""Local persistence for approved media plans (Plan Saver).

Mirrors the course pattern of ``function_tool`` side effects (``2_openai``) plus a plain
Python helper for orchestrators (similar to writing artifacts under ``6_mcp`` projects).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from agents import function_tool

from app.agents.Mediaplanner.social_plan_schema import MediaPlan


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def plans_directory() -> Path:
    d = _project_root() / "data" / "plans"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", s.strip())[:80].strip("-") or "plan"
    return s.lower()


def persist_media_plan(plan: MediaPlan, filename_slug: str) -> Path:
    """Write ``plan`` as JSON next to the app (``data/plans/``)."""
    slug = _slugify(filename_slug)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = plans_directory() / f"{slug}_{ts}.json"
    path.write_text(
        json.dumps(plan.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


@function_tool
def save_media_plan(plan_json: str, filename_slug: str = "social_plan") -> str:
    """Save a finalized media plan to local disk under data/plans/. Pass valid JSON for MediaPlan.

    Call once per plan after the calendar is complete. Use a short slug (letters, numbers, dashes).
    """
    plan = MediaPlan.model_validate_json(plan_json)
    path = persist_media_plan(plan, filename_slug)
    return f"Saved media plan to {path}"


def load_media_plan(path: str | Path) -> MediaPlan:
    """Load a plan written by :func:`persist_media_plan` (for Social Media Manager / Flow 2)."""
    p = Path(path)
    return MediaPlan.model_validate_json(p.read_text(encoding="utf-8"))


def _format_plan_for_chat(plan: MediaPlan) -> str:
    """Render a MediaPlan as readable markdown."""
    lines = [
        f"### {plan.plan_title}",
        f"**Horizon:** {plan.horizon_label}",
        "",
        f"**Content pillars:** {plan.pillar_summary}",
    ]
    if plan.cadence_notes:
        lines.append(f"\n**Cadence:** {plan.cadence_notes}")

    lines.append("\n---\n#### Content Calendar\n")
    for i, post in enumerate(plan.posts, 1):
        tags = " ".join(post.hashtags) if post.hashtags else ""
        lines.append(f"**{i}. {post.scheduled_date_hint or f'Day {post.day_index}'} — {post.platform} ({post.format})**")
        if post.time_window:
            lines.append(f"  *Post window:* {post.time_window}")
        lines.append(f"  **Hook:** {post.hook}")
        lines.append(f"  {post.caption_body}")
        if tags:
            lines.append(f"  {tags}")
        if post.media_brief:
            lines.append(f"  *Media brief:* {post.media_brief}")
        lines.append("")

    if plan.compliance_and_risk_notes:
        lines.append(f"---\n**Compliance & Risk Notes:** {plan.compliance_and_risk_notes}\n")
    if plan.metrics_to_watch:
        lines.append("**Metrics to Watch:**")
        for m in plan.metrics_to_watch:
            lines.append(f"- {m}")
        lines.append("")
    if plan.handoff_notes_for_social_manager:
        lines.append(f"**Handoff Notes:** {plan.handoff_notes_for_social_manager}\n")

    return "\n".join(lines)


@function_tool
def list_saved_plans() -> str:
    """List all saved media plans. Returns plan titles, filenames, and creation dates."""
    plan_dir = plans_directory()
    files = sorted(plan_dir.glob("*.json"), reverse=True)
    if not files:
        return "No saved media plans found."

    entries = []
    for f in files:
        try:
            plan = MediaPlan.model_validate_json(f.read_text(encoding="utf-8"))
            entries.append(f"- **{plan.plan_title}** ({plan.horizon_label}) — file: `{f.name}`")
        except Exception:
            entries.append(f"- *(unreadable)* — file: `{f.name}`")

    return f"Found {len(entries)} saved plan(s):\n\n" + "\n".join(entries)


@function_tool
def get_plan_details(filename: str) -> str:
    """Retrieve and display a specific saved media plan by its filename.

    filename: The JSON filename of the plan (e.g. 'investment-diversification-campaign_20260408T113004Z.json').
    """
    plan_dir = plans_directory()
    path = plan_dir / filename
    if not path.exists():
        available = [f.name for f in sorted(plan_dir.glob("*.json"), reverse=True)]
        return f"Plan '{filename}' not found. Available plans: {available}"

    plan = MediaPlan.model_validate_json(path.read_text(encoding="utf-8"))
    return _format_plan_for_chat(plan)
