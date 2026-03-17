"""
services/scholarship_service.py
──────────────────────────────────────────────────────────────
Scholarship Service: rule-based eligibility filter engine.
Matches student profile → eligible scholarships.
"""

from config import SCHOLARSHIPS, MAX_SCHOLARSHIPS_RETURNED
from datetime import date


def get_scholarships(filters: dict) -> dict:
    """
    Filter scholarships based on student profile.

    filters keys (all optional):
        education_level : str   e.g. "Undergraduate"
        income          : float annual income in INR
        region          : str   e.g. "Telangana"
        gender          : str   "Male" | "Female" | "Other"
        category        : str   "SC" | "ST" | "OBC" | "General" | "EWS"
        search          : str   keyword search in scheme name
        type            : str   "Scholarship" | "Internship" | "Skill Program"
    """
    edu     = filters.get("education_level", "").strip()
    income  = filters.get("income", 9999999)
    region  = filters.get("region", "").strip()
    gender  = filters.get("gender", "").strip()
    cat     = filters.get("category", "").strip()
    search  = filters.get("search", "").lower().strip()
    type_f  = filters.get("type", "").strip()

    matched = []

    for s in SCHOLARSHIPS:
        # ── Type filter
        if type_f and s["type"] != type_f:
            continue

        # ── Education level filter
        if edu and s["education_levels"] != ["All"]:
            if edu not in s["education_levels"]:
                continue

        # ── Income filter
        if income and s["income_max"] < income:
            if s["income_max"] != 9999999:
                continue

        # ── Region filter
        if region and "All India" not in s["regions"]:
            if region not in s["regions"]:
                continue

        # ── Gender filter
        if gender and s["gender"] != "All":
            if s["gender"] != gender:
                continue

        # ── Category filter
        if cat and "All" not in s["categories"]:
            if cat not in s["categories"]:
                continue

        # ── Search filter
        if search:
            if search not in s["name"].lower() and search not in s["description"].lower():
                continue

        # ── Deadline urgency
        s_copy = dict(s)
        s_copy["deadline_urgency"] = _deadline_urgency(s["deadline"])
        matched.append(s_copy)

    matched = matched[:MAX_SCHOLARSHIPS_RETURNED]

    return {
        "total":        len(matched),
        "scholarships": matched,
        "filters_applied": {k: v for k, v in filters.items() if v},
    }


def get_scholarship_by_id(sch_id: str) -> dict | None:
    for s in SCHOLARSHIPS:
        if s["id"] == sch_id:
            return s
    return None


def _deadline_urgency(deadline_str: str) -> str:
    """Return urgency level based on deadline proximity."""
    if deadline_str in ("Rolling", "Quarterly", "Discontinued/check update"):
        return "rolling"
    try:
        parts    = deadline_str.split("-")
        d        = date(int(parts[0]), int(parts[1]), int(parts[2]))
        days_left = (d - date.today()).days
        if days_left < 0:
            return "closed"
        elif days_left <= 10:
            return "urgent"
        elif days_left <= 30:
            return "soon"
        else:
            return "open"
    except Exception:
        return "open"
