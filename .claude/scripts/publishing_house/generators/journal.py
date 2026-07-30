"""Guided-journal / workbook generators + structural validators.

Contains: journal (reflective prompt pages), tracker (habit/mood grids), calendar
(monthly grids). These items are structurally verifiable (correct field shapes,
valid dates, no duplicate prompts) rather than having a hidden answer key, so
their ``verifiable`` flag stays True but the checks are structural.
"""
from __future__ import annotations

import calendar as _calendar
import random
from typing import Any

from .base import ContentType, GeneratedItem, ValidationResult, registry

_PROMPT_BANK = [
    "What is one small win from today?",
    "Name something you are grateful for right now.",
    "What drained your energy today, and why?",
    "Describe a moment you felt calm.",
    "What is one thing you want to do differently tomorrow?",
    "Who made a positive difference for you recently?",
    "What is a worry you can set down for now?",
    "What did you learn about yourself this week?",
    "Where did you show yourself kindness?",
    "What is one boundary you want to honour?",
    "What are you looking forward to?",
    "What does rest look like for you today?",
]


def generate_journal(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    prompts_per_page = int(params.get("prompts_per_page") or 2)
    bank = [p.strip() for p in (params.get("prompts") or _PROMPT_BANK) if p.strip()]
    rng.shuffle(bank)
    prompts = bank[:prompts_per_page]
    return GeneratedItem(
        content_type="journal",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={
            "prompts": prompts,
            "lines_per_prompt": int(params.get("lines_per_prompt") or 6),
            "include_date_field": bool(params.get("include_date_field", True)),
        },
        solution=None,
        metadata={"open_ended": True},
    )


def validate_journal(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="journal", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    prompts = payload.get("prompts", [])
    checks = {
        "has_prompts": len(prompts) >= 1,
        "prompts_unique": len(prompts) == len(set(prompts)),
        "prompts_nonempty": all(bool(p.strip()) for p in prompts),
        "positive_line_count": int(payload.get("lines_per_prompt", 0)) > 0,
    }
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


def generate_tracker(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    default_habits = ["Water", "Sleep", "Move", "Read", "Gratitude"]
    habits = [h.strip() for h in (params.get("habits") or default_habits) if h.strip()]
    days = int(params.get("days") or 31)
    return GeneratedItem(
        content_type="tracker",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={"habits": habits, "days": days, "style": params.get("style") or "checkbox"},
        solution=None,
        metadata={"open_ended": True, "rng_touch": rng.random()},
    )


def validate_tracker(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="tracker", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    habits = payload.get("habits", [])
    days = int(payload.get("days", 0))
    checks = {
        "has_habits": len(habits) >= 1,
        "habits_unique": len(habits) == len(set(habits)),
        "days_in_range": 1 <= days <= 31,
    }
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


def generate_calendar(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    year = int(params.get("year") or 2025)
    # Month rotates with the page index so a 12-page planner fills a year.
    month = int(params.get("month") or ((index % 12) + 1))
    first_weekday, days_in_month = _calendar.monthrange(year, month)
    weeks = _calendar.monthcalendar(year, month)
    return GeneratedItem(
        content_type="calendar",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={
            "year": year,
            "month": month,
            "month_name": _calendar.month_name[month],
            "first_weekday": first_weekday,
            "days_in_month": days_in_month,
            "weeks": weeks,
        },
        solution=None,
        metadata={"open_ended": True},
    )


def validate_calendar(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="calendar", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    year = int(payload.get("year", 0))
    month = int(payload.get("month", 0))
    checks: dict[str, bool] = {"month_in_range": 1 <= month <= 12}
    if checks["month_in_range"]:
        _, expected_days = _calendar.monthrange(year, month)
        checks["days_correct"] = int(payload.get("days_in_month", 0)) == expected_days
        flat = [day for week in payload.get("weeks", []) for day in week if day != 0]
        checks["all_days_present"] = sorted(flat) == list(range(1, expected_days + 1))
    else:
        checks["days_correct"] = False
        checks["all_days_present"] = False
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


registry.register(ContentType("journal", "journal", "Journal Prompt Page", generate_journal, validate_journal))
registry.register(ContentType("tracker", "journal", "Habit / Mood Tracker", generate_tracker, validate_tracker))
registry.register(ContentType("calendar", "journal", "Monthly Calendar", generate_calendar, validate_calendar))
