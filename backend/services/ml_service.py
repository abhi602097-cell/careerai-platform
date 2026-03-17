"""
services/ml_service.py
──────────────────────────────────────────────────────────────
ML Service: loads model artifacts once at app startup,
exposes predict() and explain() for the API routes.
"""

import numpy as np
import joblib
import json
import os
import sys
from config import (MODEL_PATH, ENCODERS_PATH, SCALER_PATH,
                    METADATA_PATH, TOP_N_CAREERS, TOP_N_XAI)

class MLService:
    _instance = None  # singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def load(self):
        if self._loaded:
            return
        print("[MLService] Loading model artifacts...")
        self.model    = joblib.load(MODEL_PATH)
        self.encoders = joblib.load(ENCODERS_PATH)
        self.scaler   = joblib.load(SCALER_PATH)
        with open(METADATA_PATH) as f:
            self.meta = json.load(f)
        self.feature_names         = self.meta["feature_names"]
        self.categorical_features  = self.meta["categorical_features"]
        self.feature_display_names = self.meta["feature_display_names"]
        self.career_classes        = self.meta["career_classes"]
        self._loaded = True
        print(f"[MLService] Ready — {len(self.career_classes)} careers, "
              f"{len(self.feature_names)} features")

    # ── Feature vector builder ────────────────────────────────────────────────
    def _build_vector(self, student: dict) -> np.ndarray:
        DEFAULTS = {
            "Age":20,"GPA":3.0,"Math_GPA":3.0,"English_GPA":3.0,
            "Science_GPA":3.0,"Social_GPA":3.0,"Aptitude_Score":65,
            "College_Credits":90,"Skills_Coding":0,"Skills_Design":0,
            "Skills_Communication":0,"Skills_Analysis":0,"Skills_Leadership":0,
            "Personality_Analytical":5.0,"Personality_Creative":5.0,
            "Personality_Social":5.0,"Preferred_Tech":5.0,
            "Preferred_Business":5.0,"Preferred_Creative":5.0,
            "Gender":"Male","Degree":"B.Tech","Education_Level":"Undergraduate",
            "Parent_Education":"Graduate","Region":"Telangana",
            "Income_Category":"2.5L-5L","Category":"General","Ethnicity":"General",
        }
        vec = []
        for feat in self.feature_names:
            raw = student.get(feat, DEFAULTS.get(feat, 0))
            if feat in self.categorical_features:
                enc = self.encoders.get(feat)
                s   = str(raw)
                val = float(enc.transform([s])[0]) if (enc and s in enc.classes_) else 0.0
            else:
                val = float(raw)
            vec.append(val)
        return self.scaler.transform(np.array(vec).reshape(1, -1))[0]

    # ── Prediction ────────────────────────────────────────────────────────────
    def predict(self, student: dict) -> dict:
        vec   = self._build_vector(student)
        proba = self.model.predict_proba(vec.reshape(1, -1))[0]
        top_idx = np.argsort(proba)[::-1][:TOP_N_CAREERS]

        predictions = []
        for rank, idx in enumerate(top_idx):
            p = float(proba[idx]) * 100
            predictions.append({
                "rank":        rank + 1,
                "career":      self.career_classes[idx],
                "probability": round(p, 2),
                "match_label": self._match_label(p),
            })

        xai = self._explain(vec, int(top_idx[0]))
        return {"predictions": predictions, "explanation": xai}

    # ── Local XAI explanation ─────────────────────────────────────────────────
    def _explain(self, vec: np.ndarray, top_career_idx: int) -> dict:
        baseline   = np.zeros_like(vec)
        base_proba = self.model.predict_proba(
            baseline.reshape(1, -1))[0][top_career_idx]

        contribs = np.zeros(len(self.feature_names))
        for i in range(len(self.feature_names)):
            p       = baseline.copy(); p[i] = vec[i]
            contribs[i] = (self.model.predict_proba(p.reshape(1, -1))[0][top_career_idx]
                           - base_proba)

        abs_c = np.abs(contribs)
        pct   = abs_c / abs_c.sum() * 100 if abs_c.sum() > 0 else abs_c
        top   = np.argsort(pct)[::-1][:TOP_N_XAI]

        factors = [
            {
                "feature":          self.feature_names[i],
                "display_name":     self.feature_display_names.get(
                                        self.feature_names[i], self.feature_names[i]),
                "contribution_pct": round(float(pct[i]), 2),
                "direction":        "positive" if contribs[i] >= 0 else "negative",
            }
            for i in top
        ]

        top_career = self.career_classes[top_career_idx]
        top3       = factors[:3]
        names      = [f["display_name"] for f in top3]
        explanation_text = (
            f"Your {', '.join(names[:2])} and {names[2]} are the strongest "
            f"indicators that {top_career} is a great fit for you."
            if len(names) >= 3 else
            f"Your profile strongly matches the {top_career} career path."
        )

        return {
            "top_career":        top_career,
            "factors":           factors,
            "explanation_text":  explanation_text,
        }

    # ── Global feature importance ─────────────────────────────────────────────
    def global_importance(self) -> list:
        if not hasattr(self.model, "feature_importances_"):
            return []
        imp   = self.model.feature_importances_
        total = imp.sum()
        pct   = imp / total * 100 if total > 0 else imp
        idx   = np.argsort(pct)[::-1]
        return [
            {
                "feature":      self.feature_names[i],
                "display_name": self.feature_display_names.get(
                                    self.feature_names[i], self.feature_names[i]),
                "importance_pct": round(float(pct[i]), 2),
            }
            for i in idx
        ]

    @staticmethod
    def _match_label(prob: float) -> str:
        if prob >= 70:   return "Excellent Match"
        elif prob >= 50: return "Strong Match"
        elif prob >= 35: return "Good Match"
        elif prob >= 20: return "Possible Match"
        return "Explore Further"


# ── Singleton instance ────────────────────────────────────────────────────────
ml_service = MLService()
