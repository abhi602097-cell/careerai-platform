"""
routes/api.py
──────────────────────────────────────────────────────────────
All API routes for the AI Student Intelligence Platform.

Endpoints:
  POST /api/v1/predict              → Career prediction + XAI
  GET  /api/v1/careers              → All careers list
  GET  /api/v1/careers/<name>       → Career details
  POST /api/v1/careers/compare      → Compare up to 3 careers
  GET  /api/v1/careers/<name>/roadmap  → Skill roadmap graph data
  GET  /api/v1/scholarships         → Filter scholarships
  GET  /api/v1/scholarships/<id>    → Single scholarship
  GET  /api/v1/resources/<career>   → Learning resources for career
  GET  /api/v1/resources/skill/<skill> → Resources for a skill
  GET  /api/v1/xai/global           → Global feature importance
  GET  /api/v1/health               → Health check
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Blueprint, request
from middleware.helpers import success, error, validate_student_input
from services.ml_service       import ml_service
from services.scholarship_service import get_scholarships, get_scholarship_by_id
from services.career_service   import (get_career_details, get_all_careers,
                                        compare_careers, get_resources_for_career,
                                        get_resources_by_skill, get_skill_roadmap)

api = Blueprint("api", __name__)


# ── Health Check ──────────────────────────────────────────────────────────────
@api.route("/health", methods=["GET"])
def health():
    return success({
        "service":  "AI Student Intelligence Platform API",
        "version":  "1.0.0",
        "ml_model": "loaded" if ml_service._loaded else "not loaded",
        "status":   "healthy",
    }, "Service is running")


# ── Career Prediction ─────────────────────────────────────────────────────────
@api.route("/predict", methods=["POST"])
def predict_career():
    """
    Predict top 3 careers for a student profile.

    Request body (JSON):
    {
        "Gender":           "Female",
        "Age":              21,
        "GPA":              3.6,
        "Math_GPA":         3.8,
        "Aptitude_Score":   82,
        "Degree":           "B.Tech",
        ... (see config.py for full list)
    }

    Response:
    {
        "predictions": [
            {"rank":1, "career":"Data Scientist", "probability":72.4, "match_label":"Strong Match"},
            ...
        ],
        "explanation": {
            "top_career": "Data Scientist",
            "factors": [{"display_name":"Aptitude Score","contribution_pct":28.4,"direction":"positive"}, ...],
            "explanation_text": "Your Aptitude Score and Tech Preference..."
        }
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return error("Request body must be valid JSON", 400)

    # Validate
    errs = validate_student_input(data)
    if errs:
        return error("Validation failed", 422, details="; ".join(errs))

    try:
        result = ml_service.predict(data)
        return success(result, f"Top {len(result['predictions'])} careers predicted")
    except Exception as e:
        return error("Prediction failed", 500, details=str(e))


# ── Career Knowledge ──────────────────────────────────────────────────────────
@api.route("/careers", methods=["GET"])
def list_careers():
    """Return all careers with basic info."""
    careers = get_all_careers()
    return success({"careers": careers, "total": len(careers)},
                   f"{len(careers)} careers available")


@api.route("/careers/<path:career_name>", methods=["GET"])
def career_details(career_name: str):
    """Return full career knowledge card."""
    career_name = career_name.replace("-", " ").title()
    details = get_career_details(career_name)
    if not details:
        return error(f"Career '{career_name}' not found", 404)
    return success(details, f"Career details for {career_name}")


@api.route("/careers/compare", methods=["POST"])
def compare():
    """
    Compare up to 3 careers side by side.
    Body: {"careers": ["Software Engineer", "Data Scientist", "ML Engineer"]}
    """
    data    = request.get_json(silent=True) or {}
    careers = data.get("careers", [])
    if not careers or not isinstance(careers, list):
        return error("Provide a 'careers' list with 1–3 career names", 400)
    result = compare_careers(careers[:3])
    return success({"comparison": result}, f"Compared {len(result)} careers")


@api.route("/careers/<path:career_name>/roadmap", methods=["GET"])
def career_roadmap(career_name: str):
    """Return skill roadmap graph data for D3.js visualization."""
    career_name = career_name.replace("-", " ").title()
    roadmap = get_skill_roadmap(career_name)
    if not roadmap["nodes"]:
        return error(f"Roadmap for '{career_name}' not found", 404)
    return success(roadmap, f"Skill roadmap for {career_name}")


# ── Scholarships ──────────────────────────────────────────────────────────────
@api.route("/scholarships", methods=["GET"])
def scholarships():
    """
    Filter scholarships by student profile.
    Query params: education_level, income, region, gender, category, search, type
    """
    filters = {
        "education_level": request.args.get("education_level", ""),
        "income":          float(request.args.get("income", 9999999)),
        "region":          request.args.get("region", ""),
        "gender":          request.args.get("gender", ""),
        "category":        request.args.get("category", ""),
        "search":          request.args.get("search", ""),
        "type":            request.args.get("type", ""),
    }
    result = get_scholarships(filters)
    return success(result, f"{result['total']} scholarships found")


@api.route("/scholarships/<sch_id>", methods=["GET"])
def scholarship_detail(sch_id: str):
    """Return single scholarship by ID."""
    sch = get_scholarship_by_id(sch_id.upper())
    if not sch:
        return error(f"Scholarship '{sch_id}' not found", 404)
    return success(sch, "Scholarship details")


# ── Learning Resources ────────────────────────────────────────────────────────
@api.route("/resources/<path:career_name>", methods=["GET"])
def resources_for_career(career_name: str):
    """
    Return learning resources for a career.
    Optional query param: type=Course|Book|Video|Certification
    """
    career_name   = career_name.replace("-", " ").title()
    resource_type = request.args.get("type", None)
    result = get_resources_for_career(career_name, resource_type)
    return success(result, f"{result['total']} resources found for {career_name}")


@api.route("/resources/skill/<skill_name>", methods=["GET"])
def resources_for_skill(skill_name: str):
    """Return all resources for a specific skill."""
    resources = get_resources_by_skill(skill_name)
    return success({"skill": skill_name, "resources": resources,
                    "total": len(resources)},
                   f"{len(resources)} resources found for {skill_name}")


# ── XAI ───────────────────────────────────────────────────────────────────────
@api.route("/xai/global", methods=["GET"])
def global_xai():
    """Return global feature importance for XAI dashboard."""
    importance = ml_service.global_importance()
    return success({"feature_importance": importance,
                    "total_features": len(importance)},
                   "Global feature importance")
