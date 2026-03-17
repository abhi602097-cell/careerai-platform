# 🎓 AI Student Intelligence Platform

An end-to-end AI-powered platform that helps students discover career paths,
scholarships, government schemes, and personalized learning resources based
on their academic profile using Machine Learning.

---

## 📁 Project Structure

```
CareerAI_Platform/
│
├── ml_pipeline/                  ← ML Model Training Pipeline
│   ├── src/
│   │   ├── preprocessing.py      Stage 1: Data cleaning, encoding, scaling
│   │   ├── train_models.py       Stage 2: Train 4 models, compare, select best
│   │   ├── explainability.py     Stage 3: Global + local XAI (SHAP-compatible)
│   │   └── inference.py          Stage 4: Real-time prediction engine
│   ├── run_pipeline.py           Master runner (runs all 4 stages)
│   ├── data/
│   │   ├── Career_Prediction_ML_Dataset_3000.xlsx   ← ML training dataset
│   │   └── Student_Master_Dataset_5000.xlsx         ← Full student dataset
│   ├── models/                   ← Trained artifacts (pkl + json)
│   │   ├── best_model.pkl        Random Forest model
│   │   ├── encoders.pkl          Label encoders for categorical features
│   │   ├── scaler.pkl            StandardScaler for numeric features
│   │   ├── metadata.json         Feature names, career classes, display names
│   │   └── best_model_info.json  Model metrics summary
│   └── output/                   ← Pipeline outputs
│       ├── model_comparison.csv
│       ├── classification_report.csv
│       ├── global_feature_importance.csv
│       └── sample_explanations.json
│
├── backend/                      ← Flask REST API Server
│   ├── app.py                    Entry point — run this to start the server
│   ├── config.py                 All settings, career & scholarship data
│   ├── requirements.txt          Python dependencies
│   ├── .env.example              Environment variables template
│   ├── routes/
│   │   └── api.py                All 11 API endpoint handlers
│   ├── services/
│   │   ├── ml_service.py         ML prediction + XAI singleton service
│   │   ├── career_service.py     Career knowledge + roadmap + resources
│   │   └── scholarship_service.py Rule-based eligibility filter engine
│   ├── middleware/
│   │   └── helpers.py            Request validation + response wrappers
│   └── models/                   ← ML artifacts (same as ml_pipeline/models)
│
├── frontend/                     ← React Frontend (dark AI dashboard)
│   ├── index.html                Standalone — works without a build step!
│   ├── package.json              For Vite build (optional)
│   └── src/services/
│       └── api.js                Backend API service layer
│
└── docs/
    ├── API_REFERENCE.md          All endpoints with examples
    ├── DATABASE_SCHEMA.md        PostgreSQL schema design
    └── DEPLOYMENT.md             Production deployment guide
```

---

## 🚀 Quick Start

### 1. Run the ML Pipeline (first time setup)
```bash
cd ml_pipeline
pip install scikit-learn pandas numpy joblib openpyxl
python run_pipeline.py
```
This trains the model and saves artifacts to `ml_pipeline/models/`.

### 2. Start the Backend API
```bash
cd backend
pip install -r requirements.txt
python app.py
# Server starts at http://localhost:5000
```

### 3. Open the Frontend
```bash
# Option A: Open directly in browser (no build needed)
open frontend/index.html

# Option B: Vite dev server
cd frontend
npm install && npm run dev
# Opens at http://localhost:5173
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/v1/health` | Health check |
| POST | `/api/v1/predict` | Career prediction + XAI |
| GET  | `/api/v1/careers` | All careers list |
| GET  | `/api/v1/careers/<name>` | Career details |
| POST | `/api/v1/careers/compare` | Compare up to 3 careers |
| GET  | `/api/v1/careers/<name>/roadmap` | D3.js skill roadmap data |
| GET  | `/api/v1/scholarships` | Filter scholarships |
| GET  | `/api/v1/scholarships/<id>` | Single scholarship |
| GET  | `/api/v1/resources/<career>` | Learning resources for career |
| GET  | `/api/v1/resources/skill/<skill>` | Resources by skill |
| GET  | `/api/v1/xai/global` | Global feature importance |

### Predict Example
```bash
curl -X POST http://localhost:5000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Gender": "Female", "Age": 21, "GPA": 3.7,
    "Math_GPA": 3.8, "Aptitude_Score": 85,
    "Degree": "B.Tech", "Education_Level": "Undergraduate",
    "Region": "Telangana", "Income_Category": "5L-8L",
    "Category": "OBC", "Ethnicity": "OBC",
    "Skills_Coding": 1, "Skills_Analysis": 1,
    "Personality_Analytical": 8.0, "Preferred_Tech": 8.5
  }'
```

---

## 🧠 ML Model Details

| Algorithm | Accuracy | Top-3 Accuracy | F1 Macro | CV Score |
|-----------|----------|----------------|----------|----------|
| Logistic Regression (Baseline) | 50.67% | 82.00% | 50.36% | 46.46% |
| **Random Forest (Selected ✓)** | **50.17%** | **82.00%** | **49.30%** | **49.71%** |
| XGBoost (HistGBM) | 48.67% | 81.33% | 48.09% | 49.62% |

**Top-3 Accuracy = 82%** — the key metric since the platform shows the top 3 predictions.

**Top Predictive Features:**
1. Creative Preference (9.84%)
2. Tech Preference (8.71%)
3. Business Preference (8.40%)
4. Creative Personality (7.28%)
5. Social Personality (7.00%)

---

## 🗄️ Database Schema (PostgreSQL)

Key tables:
- `users` — Authentication + roles (student/counselor/admin)
- `student_profiles` — Full academic + interest profile
- `career_predictions` — ML outputs + SHAP values per student
- `careers` — Career knowledge base
- `skills` + `career_skills` — Skills registry + career mapping
- `skill_dependencies` — D3.js graph dependencies
- `scholarships` — Schemes with eligibility fields
- `learning_resources` — Courses, books, videos
- `student_progress` — Skill completion tracking

---

## 🖥️ Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Home | `/` | Hero, stats, feature overview |
| AI Prediction | `/predict` | 3-section form + ML results + XAI charts |
| Career Insights | `/insights` | Career details, salary, roadmap, XAI |
| Scholarship Finder | `/scholarships` | Filtered scheme search dashboard |
| Learning Roadmap | `/learning` | Resources + progress tracker |

---

## 🚢 Production Deployment

```bash
# Backend with Gunicorn
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

# Or with Docker
docker build -t careerai-backend .
docker run -p 5000:5000 careerai-backend

# Frontend — build for production
cd frontend
npm run build
# Serve dist/ with nginx or Vercel
```

---

## 📦 Tech Stack

| Layer | Technology |
|-------|------------|
| ML | Python, Scikit-learn, Pandas, NumPy, Joblib |
| Backend | Flask 3, REST API, CORS |
| Frontend | React 18, Chart.js 4, Syne + DM Sans fonts |
| Database | PostgreSQL (schema designed) |
| Charts | Chart.js (Donut, Bar), D3.js (Roadmap graph) |
| Auth | JWT (to be added) |

---

## 👥 Target Users

- High School Students
- Undergraduate Students
- Career Switchers
- Educational Institutions
- Career Counselors

---

## 📊 Platform Modules

1. **Student Profile Engine** — Academic + interest profiling
2. **AI Career Prediction** — ML-based career matching (Top 3)
3. **Career Knowledge Engine** — Skills, tools, salary, roadmap
4. **Scholarship & Scheme Finder** — Rule-based eligibility matching
5. **Learning Resource Recommender** — Courses, books, videos per skill
6. **Explainable AI** — Feature importance charts per prediction

---

*Built with ❤️ — AI Student Intelligence Platform v1.0*
