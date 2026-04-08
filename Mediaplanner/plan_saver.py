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

from app.agents.social_plan_schema import MediaPlan


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
