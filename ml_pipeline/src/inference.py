"""
inference.py
────────────────────────────────────────────────────────────────────────────────
AI Student Intelligence Platform — Inference Engine
Stage 4 of 4: Load saved model + make real-time predictions for new students
This is what FastAPI/Flask will call when a student clicks "Predict My Career"
────────────────────────────────────────────────────────────────────────────────
"""

import numpy as np
import joblib
import json
import os
import warnings
warnings.filterwarnings("ignore")

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


class CareerPredictor:
    """
    Production-ready inference class.
    Loads model + all preprocessing artifacts once at startup.
    predict() is called per student request.
    """

    def __init__(self, models_dir: str = MODELS_DIR):
        print("[Inference] Loading model artifacts...")
        self.model    = joblib.load(os.path.join(models_dir, "best_model.pkl"))
        self.encoders = joblib.load(os.path.join(models_dir, "encoders.pkl"))
        self.scaler   = joblib.load(os.path.join(models_dir, "scaler.pkl"))

        with open(os.path.join(models_dir, "metadata.json")) as f:
            self.meta = json.load(f)

        self.feature_names         = self.meta["feature_names"]
        self.numeric_features      = self.meta["numeric_features"]
        self.categorical_features  = self.meta["categorical_features"]
        self.feature_display_names = self.meta["feature_display_names"]
        self.career_classes        = self.meta["career_classes"]

        print(f"[Inference] Ready — {self.meta['n_classes']} career classes, "
              f"{self.meta['n_features']} features")
        print(f"[Inference] Model: {joblib.load(os.path.join(models_dir, 'best_model_info.json'))}")


    def preprocess_student(self, student: dict) -> np.ndarray:
        """
        Transform raw student dict → scaled feature vector.
        Handles missing fields gracefully with sensible defaults.

        student dict example:
        {
            "Gender":           "Female",
            "Age":              21,
            "GPA":              3.6,
            "Math_GPA":         3.8,
            "English_GPA":      3.4,
            "Science_GPA":      3.7,
            "Social_GPA":       3.2,
            "Aptitude_Score":   82,
            "College_Credits":  96,
            "Degree":           "B.Tech",
            "Education_Level":  "Undergraduate",
            "Parent_Education": "Graduate",
            "Region":           "Telangana",
            "Income_Category":  "5L-8L",
            "Category":         "OBC",
            "Ethnicity":        "OBC",
            "Skills_Coding":    1,
            "Skills_Design":    0,
            "Skills_Communication": 1,
            "Skills_Analysis":  1,
            "Skills_Leadership":0,
            "Personality_Analytical": 8.0,
            "Personality_Creative":   5.0,
            "Personality_Social":     6.0,
            "Preferred_Tech":         8.5,
            "Preferred_Business":     4.0,
            "Preferred_Creative":     3.5,
        }
        """
        # Default values for missing fields
        DEFAULTS = {
            "Age": 20, "GPA": 3.0, "Math_GPA": 3.0, "English_GPA": 3.0,
            "Science_GPA": 3.0, "Social_GPA": 3.0, "Aptitude_Score": 65,
            "College_Credits": 90, "Skills_Coding": 0, "Skills_Design": 0,
            "Skills_Communication": 0, "Skills_Analysis": 0, "Skills_Leadership": 0,
            "Personality_Analytical": 5.0, "Personality_Creative": 5.0,
            "Personality_Social": 5.0, "Preferred_Tech": 5.0,
            "Preferred_Business": 5.0, "Preferred_Creative": 5.0,
            "Gender": "Male", "Degree": "B.Tech", "Education_Level": "Undergraduate",
            "Parent_Education": "Graduate", "Region": "Telangana",
            "Income_Category": "2.5L-5L", "Category": "General", "Ethnicity": "General",
        }

        feature_vector = []

        for feature in self.feature_names:
            raw_val = student.get(feature, DEFAULTS.get(feature, 0))

            if feature in self.categorical_features:
                encoder = self.encoders.get(feature)
                if encoder:
                    str_val = str(raw_val)
                    # Handle unseen categories gracefully
                    if str_val in encoder.classes_:
                        encoded = encoder.transform([str_val])[0]
                    else:
                        # Use most common class (index 0) for unknown
                        encoded = 0
                    feature_vector.append(float(encoded))
                else:
                    feature_vector.append(0.0)
            else:
                feature_vector.append(float(raw_val))

        vector = np.array(feature_vector).reshape(1, -1)
        scaled = self.scaler.transform(vector)
        return scaled[0]


    def predict(self, student: dict, top_n: int = 3) -> dict:
        """
        Main prediction method.
        Returns top N careers with probabilities + XAI explanation.
        This is the method FastAPI will call.
        """
        from explainability import explain_prediction

        vector = self.preprocess_student(student)
        proba  = self.model.predict_proba(vector.reshape(1, -1))[0]
        top_idx = np.argsort(proba)[::-1][:top_n]

        predictions = [
            {
                "rank":        i + 1,
                "career":      self.career_classes[idx],
                "probability": round(float(proba[idx]) * 100, 2),
                "match_label": self._match_label(float(proba[idx]) * 100),
            }
            for i, idx in enumerate(top_idx)
        ]

        # XAI explanation
        explanation = explain_prediction(
            vector, self.model, self.feature_names,
            self.feature_display_names, self.encoders, self.scaler
        )

        return {
            "status":      "success",
            "top_careers": predictions,
            "explanation": explanation,
        }


    def _match_label(self, prob_pct: float) -> str:
        """Convert probability % to human-readable match label."""
        if prob_pct >= 70:   return "Excellent Match"
        elif prob_pct >= 50: return "Strong Match"
        elif prob_pct >= 35: return "Good Match"
        elif prob_pct >= 20: return "Possible Match"
        else:                return "Explore Further"


# ── FastAPI-ready endpoint schema ─────────────────────────────────────────────
# This is what your FastAPI route will look like:
#
# from fastapi import FastAPI
# from pydantic import BaseModel
# from inference import CareerPredictor
#
# app       = FastAPI()
# predictor = CareerPredictor()   # loaded once at startup
#
# class StudentInput(BaseModel):
#     Gender: str
#     Age: int
#     GPA: float
#     Math_GPA: float
#     English_GPA: float
#     Science_GPA: float
#     Social_GPA: float
#     Aptitude_Score: int
#     College_Credits: int
#     Degree: str
#     Education_Level: str
#     Parent_Education: str
#     Region: str
#     Income_Category: str
#     Category: str
#     Ethnicity: str
#     Skills_Coding: int
#     Skills_Design: int
#     Skills_Communication: int
#     Skills_Analysis: int
#     Skills_Leadership: int
#     Personality_Analytical: float
#     Personality_Creative: float
#     Personality_Social: float
#     Preferred_Tech: float
#     Preferred_Business: float
#     Preferred_Creative: float
#
# @app.post("/api/predict")
# def predict_career(student: StudentInput):
#     return predictor.predict(student.dict())


# ── Test run ──────────────────────────────────────────────────────────────────
def run_inference_test():
    """Test the inference engine with a sample student."""
    print("\n" + "="*70)
    print("  INFERENCE ENGINE — TEST RUN")
    print("="*70)

    predictor = CareerPredictor()

    # Sample student profiles
    test_students = [
        {
            "name": "Arjun Sharma (B.Tech, High GPA, Strong Coder)",
            "profile": {
                "Gender": "Male", "Age": 21, "GPA": 3.8,
                "Math_GPA": 3.9, "English_GPA": 3.5, "Science_GPA": 3.8, "Social_GPA": 3.2,
                "Aptitude_Score": 88, "College_Credits": 110,
                "Degree": "B.Tech", "Education_Level": "Undergraduate",
                "Parent_Education": "Graduate", "Region": "Telangana",
                "Income_Category": "5L-8L", "Category": "OBC", "Ethnicity": "OBC",
                "Skills_Coding": 1, "Skills_Design": 0, "Skills_Communication": 1,
                "Skills_Analysis": 1, "Skills_Leadership": 0,
                "Personality_Analytical": 8.5, "Personality_Creative": 5.0, "Personality_Social": 6.0,
                "Preferred_Tech": 9.0, "Preferred_Business": 3.0, "Preferred_Creative": 2.0,
            }
        },
        {
            "name": "Priya Reddy (B.Com, Strong Business Interest)",
            "profile": {
                "Gender": "Female", "Age": 20, "GPA": 3.3,
                "Math_GPA": 3.5, "English_GPA": 3.6, "Science_GPA": 3.0, "Social_GPA": 3.8,
                "Aptitude_Score": 72, "College_Credits": 85,
                "Degree": "B.Com", "Education_Level": "Undergraduate",
                "Parent_Education": "Non-Graduate", "Region": "Maharashtra",
                "Income_Category": "2.5L-5L", "Category": "General", "Ethnicity": "General",
                "Skills_Coding": 0, "Skills_Design": 1, "Skills_Communication": 1,
                "Skills_Analysis": 1, "Skills_Leadership": 1,
                "Personality_Analytical": 6.0, "Personality_Creative": 6.5, "Personality_Social": 8.0,
                "Preferred_Tech": 4.0, "Preferred_Business": 8.5, "Preferred_Creative": 5.0,
            }
        },
        {
            "name": "Rahul Nair (M.Tech, AI Focused)",
            "profile": {
                "Gender": "Male", "Age": 24, "GPA": 3.9,
                "Math_GPA": 4.0, "English_GPA": 3.6, "Science_GPA": 3.9, "Social_GPA": 3.3,
                "Aptitude_Score": 95, "College_Credits": 150,
                "Degree": "M.Tech", "Education_Level": "Postgraduate",
                "Parent_Education": "Post-Graduate", "Region": "Karnataka",
                "Income_Category": "8L-15L", "Category": "General", "Ethnicity": "General",
                "Skills_Coding": 1, "Skills_Design": 0, "Skills_Communication": 1,
                "Skills_Analysis": 1, "Skills_Leadership": 1,
                "Personality_Analytical": 9.5, "Personality_Creative": 6.0, "Personality_Social": 5.0,
                "Preferred_Tech": 9.5, "Preferred_Business": 4.0, "Preferred_Creative": 3.0,
            }
        },
    ]

    for student_data in test_students:
        print(f"\n{'─'*60}")
        print(f"  Student: {student_data['name']}")
        print(f"{'─'*60}")

        result = predictor.predict(student_data["profile"])

        print(f"\n  TOP {len(result['top_careers'])} PREDICTED CAREERS:")
        for pred in result["top_careers"]:
            bar = "█" * int(pred["probability"] / 4)
            print(f"    {pred['rank']}. {pred['career']:<35} {bar:<25} {pred['probability']:>6.2f}%  [{pred['match_label']}]")

        print(f"\n  XAI — TOP INFLUENCING FACTORS:")
        for fc in result["explanation"]["feature_contributions"][:5]:
            direction = "↑" if fc["direction"] == "positive" else "↓"
            bar = "█" * int(fc["contribution_pct"] / 4)
            print(f"    {direction} {fc['display_name']:<30} {bar:<20} {fc['contribution_pct']:>6.2f}%")

        print(f"\n  EXPLANATION:")
        print(f"    \"{result['explanation']['explanation_text']}\"")

    print(f"\n{'='*70}")
    print("  ✓ Inference engine test complete!")
    print("="*70)


if __name__ == "__main__":
    run_inference_test()
