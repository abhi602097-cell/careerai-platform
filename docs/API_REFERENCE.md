# API Reference — AI Student Intelligence Platform

Base URL: `http://localhost:5000/api/v1`

All responses follow this format:
```json
{
  "status": "success",
  "message": "...",
  "data": { ... },
  "timestamp": "2025-10-01T10:00:00Z"
}
```

---

## POST /predict

Predict top 3 careers for a student profile.

**Request Body:**
```json
{
  "Gender": "Female",
  "Age": 21,
  "GPA": 3.7,
  "Math_GPA": 3.8,
  "English_GPA": 3.5,
  "Science_GPA": 3.6,
  "Social_GPA": 3.3,
  "Aptitude_Score": 85,
  "College_Credits": 105,
  "Degree": "B.Tech",
  "Education_Level": "Undergraduate",
  "Parent_Education": "Graduate",
  "Region": "Telangana",
  "Income_Category": "5L-8L",
  "Category": "OBC",
  "Ethnicity": "OBC",
  "Skills_Coding": 1,
  "Skills_Design": 0,
  "Skills_Communication": 1,
  "Skills_Analysis": 1,
  "Skills_Leadership": 0,
  "Personality_Analytical": 8.0,
  "Personality_Creative": 5.5,
  "Personality_Social": 6.0,
  "Preferred_Tech": 8.5,
  "Preferred_Business": 3.5,
  "Preferred_Creative": 3.0
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "predictions": [
      {"rank": 1, "career": "Data Scientist", "probability": 72.4, "match_label": "Strong Match"},
      {"rank": 2, "career": "ML Engineer",    "probability": 58.1, "match_label": "Strong Match"},
      {"rank": 3, "career": "AI Researcher",  "probability": 41.7, "match_label": "Good Match"}
    ],
    "explanation": {
      "top_career": "Data Scientist",
      "factors": [
        {"feature": "Aptitude_Score", "display_name": "Aptitude Score", "contribution_pct": 28.4, "direction": "positive"},
        {"feature": "GPA",            "display_name": "Overall GPA",    "contribution_pct": 22.1, "direction": "positive"}
      ],
      "explanation_text": "Your Aptitude Score, Overall GPA and Tech Preference are the strongest indicators..."
    }
  }
}
```

---

## GET /careers

Returns all careers with basic info.

**Response:**
```json
{
  "data": {
    "careers": [
      {"career": "Data Scientist", "job_demand": "Very High", "salary_entry": "₹5L–₹10L"},
      ...
    ],
    "total": 16
  }
}
```

---

## GET /careers/{career_name}

Returns full career knowledge card.

**Example:** `GET /careers/Data%20Scientist`

**Response:**
```json
{
  "data": {
    "career": "Data Scientist",
    "description": "...",
    "required_skills": ["Python", "Statistics", "ML", "SQL"],
    "tools": ["Pandas", "Scikit-learn", "TensorFlow"],
    "roadmap": ["Intern", "Junior DS", "Data Scientist", "Senior DS"],
    "salary": {"entry": "₹5L–₹10L", "mid": "₹12L–₹22L", "senior": "₹25L–₹50L"},
    "job_demand": "Very High"
  }
}
```

---

## POST /careers/compare

Compare up to 3 careers side by side.

**Request Body:**
```json
{"careers": ["Data Scientist", "Software Engineer", "ML Engineer"]}
```

---

## GET /careers/{career_name}/roadmap

Returns skill roadmap graph data for D3.js.

**Response:**
```json
{
  "data": {
    "career": "Data Scientist",
    "nodes": [{"id": "Python", "label": "Python", "type": "skill", "status": "not_started"}, ...],
    "edges": [{"source": "Python", "target": "Machine Learning", "type": "required"}, ...],
    "phases": [{"phase": 1, "label": "Foundation", "skills": ["Python", "SQL"]}, ...]
  }
}
```

---

## GET /scholarships

Filter scholarships. All params optional.

**Query Params:**
- `education_level` — High School / Undergraduate / Postgraduate
- `income` — Annual income in INR (float)
- `region` — Telangana / Maharashtra / etc.
- `gender` — Male / Female
- `category` — General / OBC / SC / ST / EWS
- `type` — Scholarship / Skill Program / Internship
- `search` — Keyword search

**Example:** `GET /scholarships?gender=Female&category=OBC&education_level=Undergraduate`

---

## GET /resources/{career_name}

**Query Params:**
- `type` — Course / Book / Video / Certification

**Example:** `GET /resources/Data%20Scientist?type=Course`

---

## GET /xai/global

Returns global feature importance (top features across all predictions).

**Response:**
```json
{
  "data": {
    "feature_importance": [
      {"feature": "Preferred_Creative", "display_name": "Creative Preference", "importance_pct": 9.84},
      {"feature": "Preferred_Tech",     "display_name": "Tech Preference",     "importance_pct": 8.71}
    ],
    "total_features": 27
  }
}
```

---

## Error Responses

```json
{"status": "error", "message": "Validation failed", "details": "GPA must be between 0.0 and 4.0"}
```

HTTP Codes: `200` success · `400` bad request · `404` not found · `422` validation error · `500` server error
