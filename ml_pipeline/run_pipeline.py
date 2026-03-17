"""
run_pipeline.py
────────────────────────────────────────────────────────────────────────────────
AI Student Intelligence Platform — Master Pipeline Runner
Runs all 4 stages in sequence:
  Stage 1: Preprocessing   → Clean, encode, scale data
  Stage 2: Model Training  → Train 4 models, compare, select best
  Stage 3: Explainability  → Global + per-prediction XAI
  Stage 4: Inference Test  → Validate with sample students
────────────────────────────────────────────────────────────────────────────────
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(__file__))
from src.preprocessing  import run_preprocessing
from src.train_models   import run_training
from src.explainability import run_explainability
from src.inference      import run_inference_test

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


def print_banner():
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█   AI STUDENT INTELLIGENCE PLATFORM — ML PIPELINE              █")
    print("█   Career Prediction Model v1.0                                 █")
    print("█" + " "*68 + "█")
    print("█"*70 + "\n")


def print_final_summary():
    """Print final summary of all pipeline outputs."""
    print("\n" + "="*70)
    print("  PIPELINE COMPLETE — FINAL SUMMARY")
    print("="*70)

    # Model info
    info_path = os.path.join(MODELS_DIR, "best_model_info.json")
    if os.path.exists(info_path):
        with open(info_path) as f:
            info = json.load(f)
        print(f"\n  BEST MODEL")
        print(f"  {'─'*40}")
        print(f"  Model:          {info.get('name', 'N/A')}")
        print(f"  Accuracy:       {float(info.get('accuracy',0))*100:.2f}%")
        print(f"  Top-3 Accuracy: {float(info.get('top3_accuracy',0))*100:.2f}%")
        print(f"  F1 (macro):     {float(info.get('f1_macro',0))*100:.2f}%")
        print(f"  CV Score:       {float(info.get('cv_mean',0))*100:.2f}% ± {float(info.get('cv_std',0))*100:.2f}%")

    # Metadata
    meta_path = os.path.join(MODELS_DIR, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        print(f"\n  DATASET INFO")
        print(f"  {'─'*40}")
        print(f"  Total features: {meta.get('n_features', 'N/A')}")
        print(f"  Career classes: {meta.get('n_classes', 'N/A')}")
        careers = meta.get('career_classes', [])
        print(f"  Careers mapped: {', '.join(careers[:5])} ... (+{len(careers)-5} more)")

    # Top features
    imp_path = os.path.join(OUTPUT_DIR, "global_feature_importance.csv")
    if os.path.exists(imp_path):
        import pandas as pd
        df = pd.read_csv(imp_path)
        top5 = df.head(5)
        print(f"\n  TOP 5 PREDICTIVE FEATURES")
        print(f"  {'─'*40}")
        for _, row in top5.iterrows():
            bar = "█" * int(row["Importance_Pct"] / 2)
            print(f"  {row['Feature']:<30} {bar:<20} {row['Importance_Pct']:.2f}%")

    # Saved files
    print(f"\n  SAVED ARTIFACTS")
    print(f"  {'─'*40}")
    files = {
        "models/best_model.pkl":                   "Trained ML model (load for inference)",
        "models/encoders.pkl":                     "Label encoders for all categorical features",
        "models/scaler.pkl":                       "StandardScaler for numeric features",
        "models/metadata.json":                    "Feature names, classes, display names",
        "models/best_model_info.json":             "Best model metrics",
        "output/model_comparison.csv":             "All 4 models side-by-side comparison",
        "output/classification_report.csv":        "Per-career precision / recall / F1",
        "output/global_feature_importance.csv":    "Global XAI feature importance",
        "output/per_class_importance.json":        "Per-career feature importance",
        "output/sample_explanations.json":         "Sample prediction explanations",
    }
    for fname, desc in files.items():
        full_path = os.path.join(os.path.dirname(__file__), fname)
        exists = "✓" if os.path.exists(full_path) else "✗"
        print(f"  [{exists}] {fname:<48} {desc}")

    print(f"\n{'='*70}")
    print("  Pipeline ready for FastAPI integration!")
    print("  Load model:  joblib.load('models/best_model.pkl')")
    print("  Run server:  uvicorn api:app --reload")
    print("="*70 + "\n")


if __name__ == "__main__":
    t_start = time.time()
    print_banner()

    # ── Stage 1: Preprocessing ────────────────────────────────────────────────
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│  STAGE 1 / 4  —  DATA PREPROCESSING                    │")
    print("└─────────────────────────────────────────────────────────┘")
    X_train, X_test, y_train, y_test, feature_names, encoders, scaler = run_preprocessing()

    # ── Stage 2: Model Training ───────────────────────────────────────────────
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│  STAGE 2 / 4  —  MODEL TRAINING & COMPARISON           │")
    print("└─────────────────────────────────────────────────────────┘")
    best = run_training(X_train, X_test, y_train, y_test, feature_names, encoders)

    # ── Stage 3: Explainability ───────────────────────────────────────────────
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│  STAGE 3 / 4  —  EXPLAINABILITY (XAI)                  │")
    print("└─────────────────────────────────────────────────────────┘")
    xai_results = run_explainability(
        best["model"], X_train, X_test, y_train, y_test,
        feature_names, encoders, scaler
    )

    # ── Stage 4: Inference Test ───────────────────────────────────────────────
    print("\n┌─────────────────────────────────────────────────────────┐")
    print("│  STAGE 4 / 4  —  INFERENCE ENGINE TEST                 │")
    print("└─────────────────────────────────────────────────────────┘")
    run_inference_test()

    # ── Final Summary ─────────────────────────────────────────────────────────
    elapsed = time.time() - t_start
    print(f"\n  Total pipeline time: {elapsed:.1f}s")
    print_final_summary()
