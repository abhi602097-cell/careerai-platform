"""
train_models.py
────────────────────────────────────────────────────────────────────────────────
AI Student Intelligence Platform — Model Training Pipeline
Stage 2 of 4: Train 4 ML models, compare, select best, save
Models: Logistic Regression (baseline) | Random Forest | Gradient Boosting | XGBoost (via sklearn)
────────────────────────────────────────────────────────────────────────────────
"""

import numpy as np
import pandas as pd
import joblib
import json
import os
import time
import warnings
warnings.filterwarnings("ignore")

from sklearn.linear_model    import LogisticRegression
from sklearn.ensemble        import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics         import (accuracy_score, f1_score, classification_report,
                                     confusion_matrix, top_k_accuracy_score)
from sklearn.model_selection import cross_val_score, StratifiedKFold

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Model definitions ─────────────────────────────────────────────────────────
def get_models() -> dict:
    """
    Returns all 4 candidate models with tuned hyperparameters.
    Logistic Regression = baseline.
    Random Forest & Gradient Boosting = main contenders.
    HistGradientBoosting = XGBoost-equivalent (native sklearn, faster).
    """
    from sklearn.ensemble import HistGradientBoostingClassifier

    return {
        "Logistic Regression (Baseline)": LogisticRegression(
            max_iter=1000,
            C=1.0,
            solver="lbfgs",
            random_state=42,
            n_jobs=-1,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            max_depth=20,
            min_samples_split=4,
            min_samples_leaf=2,
            max_features="sqrt",
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=6,
            min_samples_split=4,
            subsample=0.8,
            random_state=42,
        ),
        "XGBoost (HistGBM)": HistGradientBoostingClassifier(
            max_iter=300,
            learning_rate=0.1,
            max_depth=8,
            min_samples_leaf=20,
            l2_regularization=0.1,
            random_state=42,
        ),
    }


# ── Training ──────────────────────────────────────────────────────────────────
def train_single_model(name: str, model, X_train, y_train,
                       X_test, y_test) -> dict:
    """Train one model and return full metrics."""
    print(f"\n  ▶ Training: {name}")
    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0

    # Predictions
    y_pred       = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

    # Core metrics
    acc      = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro",  zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    # Top-3 accuracy (platform shows top 3 predictions)
    top3_acc = top_k_accuracy_score(y_test, y_pred_proba, k=3) if y_pred_proba is not None else None

    # Cross-validation (5-fold stratified)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv,
                                scoring="accuracy", n_jobs=-1)

    result = {
        "name":          name,
        "accuracy":      round(acc, 4),
        "f1_macro":      round(f1_macro, 4),
        "f1_weighted":   round(f1_weighted, 4),
        "top3_accuracy": round(top3_acc, 4) if top3_acc else None,
        "cv_mean":       round(cv_scores.mean(), 4),
        "cv_std":        round(cv_scores.std(), 4),
        "train_time_s":  round(train_time, 2),
        "model":         model,
        "y_pred":        y_pred,
        "y_pred_proba":  y_pred_proba,
    }

    print(f"    Accuracy:      {acc:.4f}  ({acc*100:.2f}%)")
    print(f"    Top-3 Acc:     {top3_acc:.4f}  ({top3_acc*100:.2f}%)" if top3_acc else "")
    print(f"    F1 (macro):    {f1_macro:.4f}")
    print(f"    F1 (weighted): {f1_weighted:.4f}")
    print(f"    CV Acc:        {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"    Train time:    {train_time:.2f}s")

    return result


def train_all_models(X_train, X_test, y_train, y_test) -> list[dict]:
    """Train all 4 models and return list of results."""
    print("\n" + "=" * 70)
    print("  MODEL TRAINING — 4 ALGORITHMS")
    print("=" * 70)

    models  = get_models()
    results = []

    for name, model in models.items():
        result = train_single_model(name, model, X_train, y_train, X_test, y_test)
        results.append(result)

    return results


# ── Model comparison ──────────────────────────────────────────────────────────
def compare_models(results: list[dict]) -> pd.DataFrame:
    """Build comparison table and print leaderboard."""
    print("\n" + "=" * 70)
    print("  MODEL COMPARISON LEADERBOARD")
    print("=" * 70)

    rows = []
    for r in results:
        rows.append({
            "Model":         r["name"],
            "Accuracy":      f"{r['accuracy']*100:.2f}%",
            "Top-3 Acc":     f"{r['top3_accuracy']*100:.2f}%" if r["top3_accuracy"] else "N/A",
            "F1 (macro)":    f"{r['f1_macro']*100:.2f}%",
            "F1 (weighted)": f"{r['f1_weighted']*100:.2f}%",
            "CV Mean":       f"{r['cv_mean']*100:.2f}%",
            "CV Std":        f"±{r['cv_std']*100:.2f}%",
            "Train Time":    f"{r['train_time_s']}s",
        })

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

    # Save comparison
    df.to_csv(os.path.join(OUTPUT_DIR, "model_comparison.csv"), index=False)
    print(f"\n  Saved: output/model_comparison.csv")
    return df


def select_best_model(results: list[dict]) -> dict:
    """
    Select best model based on weighted score:
    50% Top-3 Accuracy (platform shows top 3) + 30% CV Mean + 20% F1 Macro
    """
    print("\n" + "=" * 70)
    print("  BEST MODEL SELECTION")
    print("=" * 70)

    for r in results:
        top3  = r["top3_accuracy"] if r["top3_accuracy"] else r["accuracy"]
        score = (0.50 * top3) + (0.30 * r["cv_mean"]) + (0.20 * r["f1_macro"])
        r["selection_score"] = round(score, 4)

    best = max(results, key=lambda r: r["selection_score"])

    for r in results:
        marker = " ◄ BEST" if r["name"] == best["name"] else ""
        print(f"  {r['name']:<40} Score: {r['selection_score']:.4f}{marker}")

    print(f"\n  ✓ Selected: {best['name']}")
    print(f"    Accuracy:        {best['accuracy']*100:.2f}%")
    print(f"    Top-3 Accuracy:  {best['top3_accuracy']*100:.2f}%")
    print(f"    CV Score:        {best['cv_mean']*100:.2f}% ± {best['cv_std']*100:.2f}%")

    return best


# ── Save ──────────────────────────────────────────────────────────────────────
def save_best_model(best: dict, feature_names: list, encoders: dict,
                    y_test, comparison_df: pd.DataFrame):
    """Save best model + full classification report."""

    # Save model
    joblib.dump(best["model"], os.path.join(MODELS_DIR, "best_model.pkl"))
    print(f"\n  Saved: models/best_model.pkl  ({best['name']})")

    # Save all models for reference
    all_models = {}
    for key in ["name","accuracy","f1_macro","f1_weighted","top3_accuracy",
                "cv_mean","cv_std","train_time_s","selection_score"]:
        all_models[key] = best.get(key)

    with open(os.path.join(MODELS_DIR, "best_model_info.json"), "w") as f:
        json.dump(all_models, f, indent=2, default=str)

    # Classification report
    career_classes = list(encoders["Target_Career"].classes_)
    report = classification_report(
        y_test, best["y_pred"],
        target_names=career_classes,
        output_dict=True,
        zero_division=0
    )
    report_df = pd.DataFrame(report).transpose()
    report_df.to_csv(os.path.join(OUTPUT_DIR, "classification_report.csv"))
    print(f"  Saved: output/classification_report.csv")

    # Save comparison
    comparison_df.to_csv(os.path.join(OUTPUT_DIR, "model_comparison.csv"), index=False)


def run_training(X_train, X_test, y_train, y_test,
                 feature_names, encoders) -> dict:
    """Full training pipeline."""
    results       = train_all_models(X_train, X_test, y_train, y_test)
    comparison_df = compare_models(results)
    best          = select_best_model(results)
    save_best_model(best, feature_names, encoders, y_test, comparison_df)
    print("\n✓ Training complete!\n")
    return best


if __name__ == "__main__":
    from preprocessing import run_preprocessing
    X_train, X_test, y_train, y_test, feature_names, encoders, scaler = run_preprocessing()
    run_training(X_train, X_test, y_train, y_test, feature_names, encoders)
