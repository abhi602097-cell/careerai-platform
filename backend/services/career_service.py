"""
services/career_service.py
──────────────────────────────────────────────────────────────
Career Knowledge Service + Learning Resources Service.
Returns career details, roadmaps, and recommended resources.
"""

from config import CAREER_KNOWLEDGE, LEARNING_RESOURCES


# ── Career Knowledge ──────────────────────────────────────────────────────────
def get_career_details(career_name: str) -> dict | None:
    """Return full career knowledge card for a given career name."""
    data = CAREER_KNOWLEDGE.get(career_name)
    if not data:
        # Try case-insensitive match
        for key, val in CAREER_KNOWLEDGE.items():
            if key.lower() == career_name.lower():
                return {"career": key, **val}
        return None
    return {"career": career_name, **data}


def get_all_careers() -> list:
    """Return list of all career names."""
    return [{"career": k, "job_demand": v["job_demand"],
             "salary_entry": v["salary"]["entry"]}
            for k, v in CAREER_KNOWLEDGE.items()]


def compare_careers(career_names: list) -> list:
    """Return side-by-side comparison data for up to 3 careers."""
    result = []
    for name in career_names[:3]:
        details = get_career_details(name)
        if details:
            result.append({
                "career":        details["career"],
                "job_demand":    details["job_demand"],
                "salary":        details["salary"],
                "skills_count":  len(details["required_skills"]),
                "roadmap_steps": len(details["roadmap"]),
                "top_skills":    details["required_skills"][:4],
                "top_tools":     details["tools"][:4],
            })
    return result


# ── Learning Resources ────────────────────────────────────────────────────────
def get_resources_for_career(career_name: str, resource_type: str = None) -> dict:
    """
    Return all learning resources relevant to a career.
    Optionally filter by type: Course | Book | Video | Certification
    """
    # Get required skills for this career
    career_data = CAREER_KNOWLEDGE.get(career_name, {})
    required_skills = [s.lower() for s in career_data.get("required_skills", [])]
    tools           = [t.lower() for t in career_data.get("tools", [])]
    all_relevant    = required_skills + tools

    matched = []
    for res in LEARNING_RESOURCES:
        # Match by career tag
        career_match = career_name in res.get("career_tags", [])
        # Match by skill relevance
        skill_match  = res["skill"].lower() in all_relevant

        if not (career_match or skill_match):
            continue

        if resource_type and res["type"] != resource_type:
            continue

        matched.append(res)

    # Group by type
    grouped = {"Course": [], "Book": [], "Video": [], "Certification": []}
    for res in matched:
        t = res.get("type", "Course")
        if t in grouped:
            grouped[t].append(res)
        else:
            grouped.setdefault(t, []).append(res)

    return {
        "career":          career_name,
        "required_skills": career_data.get("required_skills", []),
        "resources":       matched,
        "grouped":         grouped,
        "total":           len(matched),
    }


def get_resources_by_skill(skill: str) -> list:
    """Return all resources for a specific skill."""
    return [r for r in LEARNING_RESOURCES
            if r["skill"].lower() == skill.lower()]


def get_skill_roadmap(career_name: str) -> dict:
    """
    Return structured skill roadmap for frontend D3 graph.
    Includes nodes (skills) and dependency edges.
    """
    SKILL_DEPS = {
        "Machine Learning":    ["Python", "Statistics"],
        "Deep Learning":       ["Machine Learning", "Python"],
        "Data Visualization":  ["Python", "SQL"],
        "Pandas":              ["Python"],
        "Scikit-learn":        ["Python", "Machine Learning"],
        "TensorFlow":          ["Python", "Deep Learning"],
        "Docker":              ["Linux"],
        "Kubernetes":          ["Docker"],
        "React":               ["JavaScript", "HTML", "CSS"],
        "Node.js":             ["JavaScript"],
        "MLOps":               ["Machine Learning", "Docker"],
        "AWS":                 ["Linux", "Networking"],
        "Solidity":            ["Python", "Cryptography"],
        "Flutter":             ["Dart"],
        "Power BI":            ["SQL", "Excel"],
    }

    career_data = CAREER_KNOWLEDGE.get(career_name, {})
    skills      = career_data.get("required_skills", [])
    tools       = career_data.get("tools", [])
    all_skills  = list(dict.fromkeys(skills + tools))  # deduplicated

    nodes = [{"id": s, "label": s, "type": "skill" if s in skills else "tool",
              "status": "not_started"} for s in all_skills]

    edges = []
    for skill in all_skills:
        deps = SKILL_DEPS.get(skill, [])
        for dep in deps:
            if dep in all_skills:
                edges.append({"source": dep, "target": skill, "type": "required"})

    phases = [
        {"phase": 1, "label": "Foundation",  "skills": skills[:2]  if len(skills) > 1 else skills},
        {"phase": 2, "label": "Core Skills", "skills": skills[2:5] if len(skills) > 4 else skills[2:]},
        {"phase": 3, "label": "Advanced",    "skills": skills[5:]  if len(skills) > 5 else []},
        {"phase": 4, "label": "Job Ready",   "skills": tools[:3]},
    ]
    phases = [p for p in phases if p["skills"]]

    return {
        "career": career_name,
        "nodes":  nodes,
        "edges":  edges,
        "phases": phases,
        "roadmap_steps": career_data.get("roadmap", []),
    }
