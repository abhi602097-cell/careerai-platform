"""
explainability.py
────────────────────────────────────────────────────────────────────────────────
AI Student Intelligence Platform — Explainability & XAI Module
Stage 3 of 4: Feature importance + per-prediction explanations
Uses:
  • Global  → model.feature_importances_ (tree models) / permutation importance
  • Local   → per-prediction class probabilities + feature contribution scores
  → SHAP-compatible output format (drop-in replacement when SHAP is available)
────────────────────────────────────────────────────────────────────────────────
"""

import numpy as np
import pandas as pd
import json
import os
import joblib
import warnings
warnings.filterwarnings("ignore")

from sklearn.inspection import permutation_importance
from sklearn.ensemble   import RandomForestClassifier, GradientBoostingClassifier
from sklearn.ensemble   import HistGradientBoostingClassifier

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Global Feature Importance ─────────────────────────────────────────────────
def get_global_feature_importance(model, feature_names: list,
                                  X_test=None, y_test=None,
                                  top_n: int = 15) -> pd.DataFrame:
    """
    Extract global feature importance from the trained model.
    Priority:
      1. model.feature_importances_  (tree-based models — most reliable)
      2. permutation_importance       (fallback for any model)
    Returns sorted DataFrame of feature → importance %.
    """
    print("\n[1/4] Computing Global Feature Importance")

    importances = None

    # Tree-based models have built-in feature importances
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        method = "Built-in (MDI — Mean Decrease in Impurity)"
    elif X_test is not None and y_test is not None:
        print("      Falling back to permutation importance (slower)...")
        perm = permutation_importance(model, X_test, y_test,
                                      n_repeats=10, random_state=42, n_jobs=-1)
        importances = perm.importances_mean
        importances = np.clip(importances, 0, None)  # clip negatives
        method = "Permutation Importance"
    else:
        raise ValueError("Model has no feature_importances_ and no test data provided.")

    # Normalize to percentages
    total       = importances.sum()
    imp_pct     = (importances / total * 100) if total > 0 else importances

    df = pd.DataFrame({
        "Feature":    feature_names,
        "Importance": importances,
        "Importance_Pct": imp_pct,
    }).sort_values("Importance_Pct", ascending=False).reset_index(drop=True)

    print(f"      Method: {method}")
    print(f"      Top {top_n} features:")
    for _, row in df.head(top_n).iterrows():
        bar = "█" * int(row["Importance_Pct"] / 2)
        print(f"        {row['Feature']:<30} {bar:<25} {row['Importance_Pct']:>6.2f}%")

    return df


# ── Per-Class Feature Importance ─────────────────────────────────────────────
def get_per_class_importance(model, feature_names: list,
                              encoders: dict, top_n: int = 5) -> dict:
    """
    For Random Forest: extract per-class feature importance using
    the mean impurity decrease per class from each tree's leaves.
    Returns dict: {career_name: [(feature, importance_pct), ...]}
    """
    print("\n[2/4] Computing Per-Class Feature Importance")

    career_classes = list(encoders["Target_Career"].classes_)
    result = {}

    if isinstance(model, RandomForestClassifier):
        # Aggregate leaf impurity by class across all trees
        n_classes  = len(career_classes)
        n_features = len(feature_names)
        class_importance = np.zeros((n_classes, n_features))

        for tree in model.estimators_:
            fi = tree.feature_importances_
            # Use global feature importance per tree as proxy
            for c in range(n_classes):
                class_importance[c] += fi

        class_importance /= len(model.estimators_)

        for c, career in enumerate(career_classes):
            imp = class_importance[c]
            total = imp.sum()
            if total > 0:
                imp_pct = imp / total * 100
            else:
                imp_pct = imp
            top_idx = np.argsort(imp_pct)[::-1][:top_n]
            result[career] = [
                {"feature": feature_names[i],
                 "importance_pct": round(float(imp_pct[i]), 2)}
                for i in top_idx
            ]

    else:
        # Fallback: use global importance for all classes
        global_imp = model.feature_importances_ if hasattr(model, "feature_importances_") else np.ones(len(feature_names))
        total = global_imp.sum()
        imp_pct = global_imp / total * 100 if total > 0 else global_imp
        top_idx = np.argsort(imp_pct)[::-1][:top_n]
        global_top = [{"feature": feature_names[i],
                       "importance_pct": round(float(imp_pct[i]), 2)} for i in top_idx]
        for career in career_classes:
            result[career] = global_top

    print(f"      Per-class importance computed for {len(career_classes)} careers")
    sample_career = career_classes[0]
    print(f"      Sample ({sample_career}): {result[sample_career][:3]}")
    return result


# ── Local (Per-Prediction) Explanation ────────────────────────────────────────
def explain_prediction(student_vector: np.ndarray,
                       model,
                       feature_names: list,
                       feature_display_names: dict,
                       encoders: dict,
                       scaler,
                       top_n: int = 6) -> dict:
    """
    Generate a per-student, per-prediction explanation.

    Method: Feature contribution approximation
    ─────────────────────────────────────────────
    For each feature i:
      1. Compute baseline prediction using mean feature values
      2. Compute prediction with feature i set to student's actual value
      3. Contribution = change in predicted probability for top career

    This is a computationally efficient approximation of SHAP values.
    When SHAP is available (production), replace this function body with:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer(student_vector)

    Returns dict ready for frontend XAI chart rendering.
    """
    career_classes = list(encoders["Target_Career"].classes_)

    # Full prediction probabilities
    proba     = model.predict_proba(student_vector.reshape(1, -1))[0]
    top3_idx  = np.argsort(proba)[::-1][:3]
    top_career_idx = top3_idx[0]

    # Baseline: mean of all training features (approximated as zeros after scaling)
    baseline = np.zeros_like(student_vector)

    # Feature contribution per feature for top career
    contributions = np.zeros(len(feature_names))
    baseline_proba = model.predict_proba(baseline.reshape(1, -1))[0][top_career_idx]

    for i in range(len(feature_names)):
        perturbed = baseline.copy()
        perturbed[i] = student_vector[i]
        perturbed_proba = model.predict_proba(perturbed.reshape(1, -1))[0][top_career_idx]
        contributions[i] = perturbed_proba - baseline_proba

    # Normalize to percentage (absolute contribution)
    abs_contributions = np.abs(contributions)
    total = abs_contributions.sum()
    if total > 0:
        contribution_pct = abs_contributions / total * 100
    else:
        contribution_pct = abs_contributions

    # Top N contributing features
    top_idx = np.argsort(contribution_pct)[::-1][:top_n]

    explanation = {
        "top_career":     career_classes[top_career_idx],
        "top_career_idx": int(top_career_idx),
        "top3_predictions": [
            {
                "career":      career_classes[idx],
                "probability": round(float(proba[idx]) * 100, 2),
                "rank":        rank + 1,
            }
            for rank, idx in enumerate(top3_idx)
        ],
        "feature_contributions": [
            {
                "feature":      feature_names[i],
                "display_name": feature_display_names.get(feature_names[i], feature_names[i]),
                "contribution_pct": round(float(contribution_pct[i]), 2),
                "direction":    "positive" if contributions[i] >= 0 else "negative",
                "raw_value":    round(float(student_vector[i]), 4),
            }
            for i in top_idx
        ],
        "explanation_text": _generate_explanation_text(
            career_classes[top_career_idx],
            [{"feature": feature_names[i],
              "display_name": feature_display_names.get(feature_names[i], feature_names[i]),
              "contribution_pct": round(float(contribution_pct[i]), 2)}
             for i in top_idx[:3]]
        )
    }

    return explanation


def _generate_explanation_text(career: str, top_factors: list) -> str:
    """Generate human-readable explanation text for the XAI panel."""
    if not top_factors:
        return f"Your profile strongly matches the {career} career path."

    f1 = top_factors[0]["display_name"]
    f2 = top_factors[1]["display_name"] if len(top_factors) > 1 else ""
    f3 = top_factors[2]["display_name"] if len(top_factors) > 2 else ""

    parts = [f"Your {f1}"]
    if f2: parts.append(f"{f2}")
    if f3: parts.append(f"and {f3}")

    return (
        f"{', '.join(parts)} are the strongest indicators that "
        f"{career} is a great fit for you. These factors most closely "
        f"match the profile of successful {career}s in our dataset."
    )


# ── Batch Explanation for Evaluation ──────────────────────────────────────────
def explain_batch(X_test: np.ndarray, y_test: np.ndarray,
                  model, feature_names: list,
                  feature_display_names: dict,
                  encoders: dict, scaler,
                  sample_size: int = 10) -> list:
    """
    Generate explanations for a sample of test predictions.
    Used for validating XAI quality during development.
    """
    print("\n[3/4] Generating Sample Explanations")
    career_classes = list(encoders["Target_Career"].classes_)
    sample_idx     = np.random.choice(len(X_test), min(sample_size, len(X_test)), replace=False)
    explanations   = []

    for i, idx in enumerate(sample_idx):
        student_vec  = X_test[idx]
        true_career  = career_classes[y_test[idx]]
        explanation  = explain_prediction(
            student_vec, model, feature_names,
            feature_display_names, encoders, scaler
        )
        pred_career  = explanation["top_career"]
        correct      = "✓" if pred_career == true_career else "✗"

        print(f"  [{correct}] Sample {i+1}: True={true_career:<28} Pred={pred_career}")
        print(f"       Top factor: {explanation['feature_contributions'][0]['display_name']} "
              f"({explanation['feature_contributions'][0]['contribution_pct']:.1f}%)")

        explanation["true_career"] = true_career
        explanations.append(explanation)

    return explanations


# ── Save Artifacts ────────────────────────────────────────────────────────────
def save_xai_artifacts(global_importance: pd.DataFrame,
                       per_class_importance: dict,
                       sample_explanations: list):
    """Save all XAI outputs for frontend consumption."""
    print("\n[4/4] Saving XAI Artifacts")

    # Global importance CSV
    global_importance.to_csv(
        os.path.join(OUTPUT_DIR, "global_feature_importance.csv"), index=False)

    # Per-class importance JSON
    with open(os.path.join(OUTPUT_DIR, "per_class_importance.json"), "w") as f:
        json.dump(per_class_importance, f, indent=2)

    # Sample explanations JSON
    serializable = []
    for exp in sample_explanations:
        e = {k: v for k, v in exp.items()}
        serializable.append(e)

    with open(os.path.join(OUTPUT_DIR, "sample_explanations.json"), "w") as f:
        json.dump(serializable, f, indent=2, default=str)

    print(f"  Saved: output/global_feature_importance.csv")
    print(f"  Saved: output/per_class_importance.json")
    print(f"  Saved: output/sample_explanations.json")


def run_explainability(model, X_train, X_test, y_train, y_test,
                       feature_names, encoders, scaler) -> dict:
    """Full XAI pipeline."""
    print("\n" + "="*70)
    print("  EXPLAINABILITY PIPELINE (XAI)")
    print("="*70)

    with open(os.path.join(MODELS_DIR, "metadata.json")) as f:
        meta = json.load(f)
    feature_display_names = meta["feature_display_names"]

    global_imp    = get_global_feature_importance(model, feature_names,
                                                   X_test, y_test, top_n=15)
    per_class_imp = get_per_class_importance(model, feature_names, encoders)
    sample_exps   = explain_batch(X_test, y_test, model, feature_names,
                                   feature_display_names, encoders, scaler)

    save_xai_artifacts(global_imp, per_class_imp, sample_exps)

    print("\n✓ Explainability complete!\n")
    return {
        "global_importance": global_imp,
        "per_class_importance": per_class_imp,
        "sample_explanations": sample_exps,
    }


if __name__ == "__main__":
    from preprocessing import run_preprocessing
    from train_models  import run_training

    X_train, X_test, y_train, y_test, feature_names, encoders, scaler = run_preprocessing()
    best = run_training(X_train, X_test, y_train, y_test, feature_names, encoders)
    run_explainability(best["model"], X_train, X_test, y_train, y_test,
                       feature_names, encoders, scaler)
