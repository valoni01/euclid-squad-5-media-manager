from typing import Literal

from pydantic import BaseModel, Field


class PlannedPost(BaseModel):
    """One scheduled social post in the calendar."""

    day_index: int = Field(
        ge=0,
        description="0-based day offset within the planning window (day 0 = first day).",
    )
    scheduled_date_hint: str = Field(
        default="",
        description="Optional ISO date or label like 'Week 2 Wednesday'.",
    )
    platform: str = Field(
        description="e.g. Instagram, LinkedIn, TikTok, X, YouTube Shorts.",
    )
    format: Literal["image", "video", "carousel", "text", "reel", "story", "thread", "live"] = (
        "text"
    )
    hook: str = Field(description="Scroll-stopping first line or on-screen hook.")
    caption_body: str = Field(description="Main caption or script outline.")
    hashtags: list[str] = Field(default_factory=list)
    media_brief: str = Field(
        default="",
        description="Directions for the media (photo/video) agent: subjects, style, length, B-roll.",
    )
    time_window: str = Field(
        default="",
        description="Suggested posting window in brand local time, e.g. '09:00–11:00'.",
    )


class MediaPlan(BaseModel):
    """Full social calendar and strategy for a fixed horizon."""

    plan_title: str
    horizon_label: str = Field(
        description="Human-readable window, e.g. '14 days starting 2026-04-15'.",
    )
    pillar_summary: str = Field(
        description="Content pillars and themes tied to the analyst guidance.",
    )
    cadence_notes: str = Field(
        default="",
        description="Posting cadence, mix of formats, and platform priorities.",
    )
    posts: list[PlannedPost] = Field(
        description="Ordered list covering the horizon; keep realistic volume.",
    )
    compliance_and_risk_notes: str = Field(
        default="",
        description="Claims to avoid, disclosures, brand-safety, regulated-industry notes.",
    )
    metrics_to_watch: list[str] = Field(
        default_factory=list,
        description="KPIs or experiments to track for this plan.",
    )
    handoff_notes_for_social_manager: str = Field(
        default="",
        description="What the Social Media Manager should execute, approve, or schedule first.",
    )
