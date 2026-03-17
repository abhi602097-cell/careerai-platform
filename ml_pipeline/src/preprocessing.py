"""
preprocessing.py
────────────────────────────────────────────────────────────────────────────────
AI Student Intelligence Platform — Data Preprocessing Pipeline
Stage 1 of 4: Raw data → Cleaned, encoded, scaled features ready for ML
────────────────────────────────────────────────────────────────────────────────
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "Career_Prediction_ML_Dataset_3000.xlsx")
OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), "..", "output")
MODELS_DIR  = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# ── Feature definitions ───────────────────────────────────────────────────────
NUMERIC_FEATURES = [
    "Age", "GPA", "Math_GPA", "English_GPA", "Science_GPA", "Social_GPA",
    "Aptitude_Score", "College_Credits",
    "Skills_Coding", "Skills_Design", "Skills_Communication",
    "Skills_Analysis", "Skills_Leadership",
    "Personality_Analytical", "Personality_Creative", "Personality_Social",
    "Preferred_Tech", "Preferred_Business", "Preferred_Creative"
]

CATEGORICAL_FEATURES = [
    "Gender", "Degree", "Education_Level", "Parent_Education",
    "Region", "Income_Category", "Category", "Ethnicity"
]

ALL_FEATURES   = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_COL     = "Target_Career"
CATEGORY_COL   = "Career_Category"

# Human-readable display names for XAI charts
FEATURE_DISPLAY_NAMES = {
    "Age":                    "Age",
    "GPA":                    "Overall GPA",
    "Math_GPA":               "Math GPA",
    "English_GPA":            "English GPA",
    "Science_GPA":            "Science GPA",
    "Social_GPA":             "Social Science GPA",
    "Aptitude_Score":         "Aptitude Score",
    "College_Credits":        "College Credits",
    "Skills_Coding":          "Coding Skills",
    "Skills_Design":          "Design Skills",
    "Skills_Communication":   "Communication Skills",
    "Skills_Analysis":        "Analytical Skills",
    "Skills_Leadership":      "Leadership Skills",
    "Personality_Analytical": "Analytical Personality",
    "Personality_Creative":   "Creative Personality",
    "Personality_Social":     "Social Personality",
    "Preferred_Tech":         "Tech Preference",
    "Preferred_Business":     "Business Preference",
    "Preferred_Creative":     "Creative Preference",
    "Gender":                 "Gender",
    "Degree":                 "Degree",
    "Education_Level":        "Education Level",
    "Parent_Education":       "Parent Education",
    "Region":                 "Region",
    "Income_Category":        "Income Category",
    "Category":               "Social Category",
    "Ethnicity":              "Ethnicity",
}


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    """Load raw dataset from Excel."""
    print(f"[1/7] Loading data from: {path}")
    df = pd.read_excel(path, header=1)
    print(f"      Loaded {len(df)} rows × {len(df.columns)} columns")
    return df


def inspect_data(df: pd.DataFrame) -> dict:
    """Basic data quality report."""
    print("\n[2/7] Data Inspection")
    report = {}

    # Missing values
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    report["missing_values"] = missing.to_dict()
    print(f"      Missing values: {len(missing)} columns affected")
    if len(missing):
        for col, cnt in missing.items():
            print(f"        → {col}: {cnt} missing ({cnt/len(df)*100:.1f}%)")

    # Target distribution
    if TARGET_COL in df.columns:
        dist = df[TARGET_COL].value_counts()
        report["target_distribution"] = dist.to_dict()
        print(f"      Target classes: {len(dist)} unique careers")
        print(f"      Class balance: min={dist.min()}, max={dist.max()}, mean={dist.mean():.1f}")

    # Numeric summary
    report["shape"] = df.shape
    print(f"      Dataset shape: {df.shape}")
    return report


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw data:
    - Drop duplicates
    - Handle missing values
    - Fix data types
    - Remove outliers
    """
    print("\n[3/7] Cleaning Data")
    original_len = len(df)

    # Drop duplicates
    df = df.drop_duplicates(subset=["Student_ID"]) if "Student_ID" in df.columns else df.drop_duplicates()
    print(f"      Duplicates removed: {original_len - len(df)}")

    # Drop non-feature columns
    drop_cols = ["Student_ID", CATEGORY_COL]
    drop_cols = [c for c in drop_cols if c in df.columns]
    df = df.drop(columns=drop_cols)

    # Fill missing numeric values with median
    for col in NUMERIC_FEATURES:
        if col in df.columns and df[col].isnull().any():
            median = df[col].median()
            df[col] = df[col].fillna(median)
            print(f"      Filled '{col}' nulls with median={median:.2f}")

    # Fill missing categorical values with mode
    for col in CATEGORICAL_FEATURES:
        if col in df.columns and df[col].isnull().any():
            mode = df[col].mode()[0]
            df[col] = df[col].fillna(mode)
            print(f"      Filled '{col}' nulls with mode='{mode}'")

    # Clamp GPA to [0, 4.0]
    for gpa_col in ["GPA","Math_GPA","English_GPA","Science_GPA","Social_GPA"]:
        if gpa_col in df.columns:
            df[gpa_col] = df[gpa_col].clip(0.0, 4.0)

    # Clamp Aptitude_Score to [0, 100]
    if "Aptitude_Score" in df.columns:
        df["Aptitude_Score"] = df["Aptitude_Score"].clip(0, 100)

    # Clamp personality/preference scores to [0, 10]
    for col in ["Personality_Analytical","Personality_Creative","Personality_Social",
                "Preferred_Tech","Preferred_Business","Preferred_Creative"]:
        if col in df.columns:
            df[col] = df[col].clip(0, 10)

    # Clamp binary skill flags to [0, 1]
    for col in ["Skills_Coding","Skills_Design","Skills_Communication",
                "Skills_Analysis","Skills_Leadership"]:
        if col in df.columns:
            df[col] = df[col].clip(0, 1)

    print(f"      Clean dataset: {len(df)} rows")
    return df


def encode_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Encode categorical features using LabelEncoder.
    Returns encoded df + dict of fitted encoders (saved for inference).
    """
    print("\n[4/7] Encoding Categorical Features")
    encoders = {}

    for col in CATEGORICAL_FEATURES:
        if col not in df.columns:
            continue
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
        print(f"      '{col}' → {len(le.classes_)} classes encoded")

    # Encode target
    le_target = LabelEncoder()
    df[TARGET_COL] = le_target.fit_transform(df[TARGET_COL].astype(str))
    encoders[TARGET_COL] = le_target
    print(f"      Target '{TARGET_COL}' → {len(le_target.classes_)} career classes")
    print(f"      Career classes: {list(le_target.classes_)}")

    return df, encoders


def scale_features(X_train: np.ndarray, X_test: np.ndarray,
                   feature_names: list) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    """
    Scale numeric features using StandardScaler.
    Fitted only on training data to prevent data leakage.
    """
    print("\n[5/7] Scaling Features")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    print(f"      StandardScaler fitted on {X_train.shape[0]} training samples")
    print(f"      Feature means (top 5): {dict(zip(feature_names[:5], scaler.mean_[:5].round(3)))}")
    return X_train_scaled, X_test_scaled, scaler


def split_data(df: pd.DataFrame) -> tuple:
    """
    Split into features (X) and target (y), then train/test split.
    """
    print("\n[6/7] Splitting Dataset")

    # Keep only features that exist
    available_features = [f for f in ALL_FEATURES if f in df.columns]
    missing_features   = [f for f in ALL_FEATURES if f not in df.columns]
    if missing_features:
        print(f"      Warning: Missing features → {missing_features}")

    X = df[available_features].values
    y = df[TARGET_COL].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"      Features used: {len(available_features)}")
    print(f"      Train set: {X_train.shape[0]} samples")
    print(f"      Test  set: {X_test.shape[0]} samples")
    print(f"      Class distribution train — unique: {len(np.unique(y_train))}")

    return X_train, X_test, y_train, y_test, available_features


def save_artifacts(encoders: dict, scaler: StandardScaler,
                   feature_names: list, report: dict):
    """Save all preprocessing artifacts for use during inference."""
    print("\n[7/7] Saving Preprocessing Artifacts")

    joblib.dump(encoders, os.path.join(MODELS_DIR, "encoders.pkl"))
    joblib.dump(scaler,   os.path.join(MODELS_DIR, "scaler.pkl"))

    meta = {
        "feature_names":        feature_names,
        "numeric_features":     NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "target_col":           TARGET_COL,
        "feature_display_names": FEATURE_DISPLAY_NAMES,
        "career_classes":       list(encoders[TARGET_COL].classes_),
        "n_features":           len(feature_names),
        "n_classes":            len(encoders[TARGET_COL].classes_),
        "data_report":          report,
    }
    with open(os.path.join(MODELS_DIR, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2, default=str)

    print(f"      Saved: encoders.pkl, scaler.pkl, metadata.json")
    print(f"      Location: {MODELS_DIR}")


def run_preprocessing() -> tuple:
    """Full preprocessing pipeline. Returns train/test splits + metadata."""
    print("=" * 70)
    print("  AI STUDENT PLATFORM — PREPROCESSING PIPELINE")
    print("=" * 70)

    df            = load_data()
    report        = inspect_data(df)
    df            = clean_data(df)
    df, encoders  = encode_features(df)

    X_train, X_test, y_train, y_test, feature_names = split_data(df)

    X_train_sc, X_test_sc, scaler = scale_features(X_train, X_test, feature_names)

    save_artifacts(encoders, scaler, feature_names, report)

    print("\n✓ Preprocessing complete!\n")
    return X_train_sc, X_test_sc, y_train, y_test, feature_names, encoders, scaler


if __name__ == "__main__":
    run_preprocessing()
