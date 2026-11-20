"""Transparent, deterministic job-fit scoring; not an employment prediction."""
from __future__ import annotations

import re
from typing import Any

SKILL_ALIASES = {
    "python": ("python",),
    "sql": ("sql",),
    "pandas": ("pandas",),
    "numpy": ("numpy",),
    "scikit-learn": ("scikit-learn", "sklearn"),
    "pytorch": ("pytorch", "torch"),
    "tensorflow": ("tensorflow",),
    "fastapi": ("fastapi",),
    "flask": ("flask",),
    "rest api": ("rest api", "restful api", "api development"),
    "git": ("git", "github"),
    "docker": ("docker",),
    "linux": ("linux",),
    "llm": ("llm", "large language model"),
    "generative ai": ("generative ai", "genai", "gen ai"),
    "langchain": ("langchain",),
    "rag": ("rag", "retrieval augmented generation"),
    "streamlit": ("streamlit",),
    "machine learning": ("machine learning", "ml engineer", "ml/ai"),
    "deep learning": ("deep learning",),
    "javascript": ("javascript",),
    "react": ("react",),
    "java": ("java",),
    "aws": ("aws", "amazon web services"),
    "azure": ("azure",),
    "kubernetes": ("kubernetes", "k8s"),
    "pytest": ("pytest",),
}

def _text(value: Any) -> str:
    return str(value or "").lower()

def _skills(value: Any) -> set[str]:
    text = _text(value)
    return {skill for skill, aliases in SKILL_ALIASES.items()
            if any(alias in text for alias in aliases)}

def score_job(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Return a reproducible 0-100 fit score plus matched skills and gaps."""
    description = " ".join([
        _text(job.get("title")), _text(job.get("description")),
        _text(job.get("company")),
    ])
    candidate_text = " ".join([
        _text(profile.get("skills")), _text(profile.get("experience")),
        _text(profile.get("projects")), _text(profile.get("education")),
    ])
    candidate_skills = _skills(candidate_text)
    required_skills = _skills(description)
    matched = sorted(candidate_skills & required_skills)
    gaps = sorted(required_skills - candidate_skills)

    if required_skills:
        skill_points = 50 * len(matched) / len(required_skills)
    else:
        skill_points = 25.0

    title = _text(job.get("title"))
    targets = profile.get("target_roles", [])
    if isinstance(targets, str):
        targets = [x.strip() for x in re.split(r"[,\n]", targets) if x.strip()]
    role_hits = sum(1 for target in targets if _text(target) and _text(target) in title)
    role_points = min(20.0, 20.0 * role_hits / max(1, len(targets))) if targets else 10.0

    location = _text(job.get("location"))
    target_locations = profile.get("target_locations", ["Bengaluru", "Hyderabad"])
    if isinstance(target_locations, str):
        target_locations = [x.strip() for x in re.split(r"[,\n]", target_locations) if x.strip()]
    if not location or not target_locations:
        location_points = 7.0
    else:
        location_points = 15.0 if any(_text(x) in location for x in target_locations) else 3.0

    experience_points = 10.0
    candidate_years = profile.get("years_experience")
    exp_match = re.search(r"(\d+)\s*\+?\s*(?:years?|yrs?)", description)
    if exp_match and candidate_years is not None:
        required_years = int(exp_match.group(1))
        try:
            candidate_years_num = float(candidate_years)
            if required_years > candidate_years_num:
                experience_points = 2.0
        except (TypeError, ValueError):
            pass

    score = round(min(100.0, skill_points + role_points + location_points + experience_points))
    reasons = [
        f"{len(matched)} of {len(required_skills)} detected skills overlap" if required_skills
        else "No explicit skills were detected in the job text",
        "Target location matches" if location_points == 15 else "Location match is uncertain or outside target cities",
        "Target role matches" if role_hits else "Role title does not exactly match a saved target role",
    ]
    return {
        "score": score,
        "matched_skills": matched,
        "skill_gaps": gaps,
        "reasons": reasons,
        "note": "Heuristic fit indicator only. Verify experience requirements and the employer's official listing.",
    }
