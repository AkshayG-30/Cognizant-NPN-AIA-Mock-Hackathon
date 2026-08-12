"""
============================================================
CarePath AI — Wait-Time Model V2 Inference / Testing
============================================================

V2 model expects exactly 13 features:

    arrival_rate_7d
    queue_length_at_booking
    queue_pressure
    sched_day_of_week
    dow_sin
    dow_cos
    month_sin
    slot_minute
    sched_week_of_year
    month_cos
    sched_day_of_month
    sched_quarter
    slot_hour

IMPORTANT:
    This script intentionally does NOT use the old V1
    features such as:

        utilization
        active_backlog
        server_count
        service_rate
        org_size
        telehealth
        specialty_encoded

    because the V2 model does not use them.

Run:

    d:\\CTS Mock\\venv\\Scripts\\python.exe ^
    d:\\CTS Mock\\models\\test\\test_wait_time.py
"""

import json
import math
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(r"D:\CTS Mock")

ARTIFACTS = (
    PROJECT_ROOT
    / "models"
    / "artifacts"
    / "v2"
)

MODEL_PATH = (
    ARTIFACTS
    / "wait_time_lgbm_v2.txt"
)

FEATURE_MANIFEST_PATH = (
    ARTIFACTS
    / "v2_feature_manifest.json"
)


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 80)
print("CAREPATH AI — WAIT-TIME MODEL V2 TEST")
print("=" * 80)

print("\nArtifact configuration")
print("-" * 80)

print(f"Model       : {MODEL_PATH}")
print(f"Feature map : {FEATURE_MANIFEST_PATH}")


if not MODEL_PATH.exists():

    raise FileNotFoundError(
        f"\nV2 model not found:\n{MODEL_PATH}"
    )


if not FEATURE_MANIFEST_PATH.exists():

    raise FileNotFoundError(
        f"\nV2 feature manifest not found:\n"
        f"{FEATURE_MANIFEST_PATH}"
    )


# ============================================================
# LOAD LIGHTGBM MODEL
# ============================================================

print("\nLoading LightGBM V2 model...")

model = lgb.Booster(
    model_file=str(MODEL_PATH)
)

print("Model loaded successfully.")

print(
    f"Number of trees : {model.num_trees()}"
)

print(
    f"Number of feats : {model.num_feature()}"
)


# ============================================================
# LOAD FEATURE MANIFEST
# ============================================================

with open(
    FEATURE_MANIFEST_PATH,
    "r",
    encoding="utf-8"
) as f:

    manifest = json.load(f)


# Support common manifest formats
if isinstance(manifest, list):

    feature_cols = manifest

elif isinstance(manifest, dict):

    if "features" in manifest:

        feature_cols = manifest["features"]

    elif "selected_features" in manifest:

        feature_cols = manifest["selected_features"]

    elif "feature_columns" in manifest:

        feature_cols = manifest["feature_columns"]

    else:

        raise ValueError(
            "Could not find feature list in "
            "v2_feature_manifest.json"
        )

else:

    raise ValueError(
        "Invalid feature manifest format."
    )


feature_cols = list(feature_cols)

model_features = list(
    model.feature_name()
)


# ============================================================
# FEATURE SCHEMA VALIDATION
# ============================================================

print("\nFeatures expected by the V2 model:")
print("-" * 80)

for i, feature in enumerate(
    model_features,
    start=1
):

    print(
        f"{i:>2}. {feature}"
    )


print(
    f"\nLoaded {len(feature_cols)} "
    f"features from V2 manifest."
)


if feature_cols != model_features:

    print(
        "\nWARNING: Manifest ordering differs "
        "from LightGBM model ordering."
    )

    # Use LightGBM's actual ordering.
    feature_cols = model_features


else:

    print(
        "Feature schema validation: PASSED"
    )


# ============================================================
# EXPECTED V2 FEATURES
# ============================================================

EXPECTED_FEATURES = [
    "arrival_rate_7d",
    "queue_length_at_booking",
    "queue_pressure",
    "sched_day_of_week",
    "dow_sin",
    "dow_cos",
    "month_sin",
    "slot_minute",
    "sched_week_of_year",
    "month_cos",
    "sched_day_of_month",
    "sched_quarter",
    "slot_hour",
]


# ============================================================
# FINAL SAFETY CHECK
# ============================================================

if set(model_features) != set(EXPECTED_FEATURES):

    raise ValueError(
        "\nMODEL FEATURE SCHEMA DOES NOT MATCH EXPECTED V2 SCHEMA.\n\n"
        f"Expected:\n{EXPECTED_FEATURES}\n\n"
        f"Actual:\n{model_features}\n"
    )


print(
    "\nV2 feature schema confirmed."
)


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def build_features(
    arrival_rate_7d,
    queue_length_at_booking,
    day_of_week=1,
    month=6,
    week_of_year=None,
    day_of_month=15,
    quarter=None,
    slot_hour=10,
    slot_minute=0,
):
    """
    Build EXACTLY the 13 features expected by V2.

    Parameters
    ----------
    arrival_rate_7d:
        Recent 7-day arrival/request rate.

    queue_length_at_booking:
        Queue length at the time of booking.

    day_of_week:
        0 = Monday
        1 = Tuesday
        ...
        6 = Sunday

    month:
        1-12

    week_of_year:
        ISO week number 1-53.

    day_of_month:
        1-31

    quarter:
        1-4

    slot_hour:
        0-23

    slot_minute:
        0-59
    """

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not 0 <= day_of_week <= 6:

        raise ValueError(
            "day_of_week must be between 0 and 6."
        )

    if not 1 <= month <= 12:

        raise ValueError(
            "month must be between 1 and 12."
        )

    if not 0 <= slot_hour <= 23:

        raise ValueError(
            "slot_hour must be between 0 and 23."
        )

    if not 0 <= slot_minute <= 59:

        raise ValueError(
            "slot_minute must be between 0 and 59."
        )

    if not 1 <= day_of_month <= 31:

        raise ValueError(
            "day_of_month must be between 1 and 31."
        )

    # --------------------------------------------------------
    # Automatically derive week if not supplied.
    #
    # This is only for manual testing.
    # For production inference, use the actual booking date.
    # --------------------------------------------------------

    if week_of_year is None:

        # Approximate week based on month/day.
        # Production should use datetime.isocalendar().
        approximate_date = pd.Timestamp(
            year=2024,
            month=month,
            day=min(day_of_month, 28)
        )

        week_of_year = int(
            approximate_date.isocalendar().week
        )

    # --------------------------------------------------------
    # Derive quarter
    # --------------------------------------------------------

    if quarter is None:

        quarter = (
            (month - 1) // 3
        ) + 1

    # --------------------------------------------------------
    # Cyclical day-of-week encoding
    # --------------------------------------------------------

    dow_sin = math.sin(
        2 * math.pi * day_of_week / 7
    )

    dow_cos = math.cos(
        2 * math.pi * day_of_week / 7
    )

    # --------------------------------------------------------
    # Cyclical month encoding
    # --------------------------------------------------------

    month_sin = math.sin(
        2 * math.pi * (month - 1) / 12
    )

    month_cos = math.cos(
        2 * math.pi * (month - 1) / 12
    )

    # --------------------------------------------------------
    # Queue pressure
    #
    # IMPORTANT:
    # This must match the formula used during V2 training.
    #
    # Based on the V2 feature design, queue pressure is
    # represented as queue relative to recent arrival rate.
    # --------------------------------------------------------

    queue_pressure = (
        queue_length_at_booking
        /
        max(float(arrival_rate_7d), 0.01)
    )

    # --------------------------------------------------------
    # Create feature dictionary
    # --------------------------------------------------------

    features = {

        "arrival_rate_7d":
            float(arrival_rate_7d),

        "queue_length_at_booking":
            float(queue_length_at_booking),

        "queue_pressure":
            float(queue_pressure),

        "sched_day_of_week":
            int(day_of_week),

        "dow_sin":
            float(dow_sin),

        "dow_cos":
            float(dow_cos),

        "month_sin":
            float(month_sin),

        "slot_minute":
            int(slot_minute),

        "sched_week_of_year":
            int(week_of_year),

        "month_cos":
            float(month_cos),

        "sched_day_of_month":
            int(day_of_month),

        "sched_quarter":
            int(quarter),

        "slot_hour":
            int(slot_hour),
    }

    # --------------------------------------------------------
    # Create dataframe
    # --------------------------------------------------------

    df = pd.DataFrame(
        [features]
    )

    # --------------------------------------------------------
    # Verify all required columns exist
    # --------------------------------------------------------

    missing = [
        feature
        for feature in model_features
        if feature not in df.columns
    ]

    if missing:

        raise ValueError(
            "Missing V2 features:\n"
            + "\n".join(
                f"  - {x}"
                for x in missing
            )
        )

    # --------------------------------------------------------
    # EXACT MODEL ORDER
    # --------------------------------------------------------

    df = df[
        model_features
    ]

    # --------------------------------------------------------
    # Numeric validation
    # --------------------------------------------------------

    values = df.to_numpy(
        dtype=float
    )

    if not np.isfinite(values).all():

        raise ValueError(
            "Feature vector contains "
            "NaN or infinite values."
        )

    return df


# ============================================================
# PREDICTION
# ============================================================

def predict_wait(
    arrival_rate_7d,
    queue_length_at_booking,
    day_of_week=1,
    month=6,
    week_of_year=None,
    day_of_month=15,
    quarter=None,
    slot_hour=10,
    slot_minute=0,
):
    """
    Predict booking lead time in days.
    """

    features = build_features(

        arrival_rate_7d=
            arrival_rate_7d,

        queue_length_at_booking=
            queue_length_at_booking,

        day_of_week=
            day_of_week,

        month=
            month,

        week_of_year=
            week_of_year,

        day_of_month=
            day_of_month,

        quarter=
            quarter,

        slot_hour=
            slot_hour,

        slot_minute=
            slot_minute,
    )

    prediction = model.predict(
        features
    )[0]

    return float(prediction)


# ============================================================
# PREDEFINED TEST SCENARIOS
# ============================================================

print("\n")
print("=" * 80)
print("V2 TEST SCENARIOS")
print("=" * 80)


scenarios = [

    {
        "name":
            "Low queue / low demand",

        "arrival_rate_7d":
            20,

        "queue_length_at_booking":
            1,

        "day_of_week":
            0,

        "month":
            3,

        "day_of_month":
            4,

        "slot_hour":
            9,

        "slot_minute":
            0,
    },

    {
        "name":
            "Moderate queue / moderate demand",

        "arrival_rate_7d":
            30,

        "queue_length_at_booking":
            4,

        "day_of_week":
            2,

        "month":
            6,

        "day_of_month":
            12,

        "slot_hour":
            10,

        "slot_minute":
            30,
    },

    {
        "name":
            "High queue / high demand",

        "arrival_rate_7d":
            45,

        "queue_length_at_booking":
            8,

        "day_of_week":
            4,

        "month":
            1,

        "day_of_month":
            10,

        "slot_hour":
            15,

        "slot_minute":
            0,
    },

    {
        "name":
            "Very high queue / stressed system",

        "arrival_rate_7d":
            50,

        "queue_length_at_booking":
            15,

        "day_of_week":
            0,

        "month":
            12,

        "day_of_month":
            2,

        "slot_hour":
            14,

        "slot_minute":
            30,
    },

    {
        "name":
            "Low queue / Friday",

        "arrival_rate_7d":
            20,

        "queue_length_at_booking":
            1,

        "day_of_week":
            4,

        "month":
            5,

        "day_of_month":
            17,

        "slot_hour":
            11,

        "slot_minute":
            0,
    },

    {
        "name":
            "High queue / Monday",

        "arrival_rate_7d":
            45,

        "queue_length_at_booking":
            10,

        "day_of_week":
            0,

        "month":
            9,

        "day_of_month":
            9,

        "slot_hour":
            8,

        "slot_minute":
            30,
    },
]


# ============================================================
# RUN SCENARIOS
# ============================================================

results = []

print(
    f"\n{'Scenario':<38}"
    f"{'Arrival 7d':>12}"
    f"{'Queue':>10}"
    f"{'Pressure':>12}"
    f"{'Wait':>14}"
)

print("-" * 90)


for scenario in scenarios:

    scenario = scenario.copy()

    name = scenario.pop(
        "name"
    )

    features = build_features(
        **scenario
    )

    wait = predict_wait(
        **scenario
    )

    pressure = float(
        features[
            "queue_pressure"
        ].iloc[0]
    )

    print(
        f"{name:<38}"
        f"{scenario['arrival_rate_7d']:>12.1f}"
        f"{scenario['queue_length_at_booking']:>10.1f}"
        f"{pressure:>12.3f}"
        f"{wait:>11.2f} days"
    )

    results.append({
        "scenario":
            name,

        "arrival_rate_7d":
            scenario["arrival_rate_7d"],

        "queue_length":
            scenario["queue_length_at_booking"],

        "queue_pressure":
            pressure,

        "predicted_wait_days":
            wait,
    })


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("\n")
print("=" * 80)
print("V2 FEATURE IMPORTANCE — GAIN")
print("=" * 80)

importance = model.feature_importance(
    importance_type="gain"
)

importance_df = pd.DataFrame({
    "feature":
        model_features,

    "gain":
        importance,
})

importance_df = importance_df.sort_values(
    "gain",
    ascending=False
)

for _, row in importance_df.iterrows():

    print(
        f"{row['feature']:<35}"
        f"{row['gain']:>18,.2f}"
    )


# ============================================================
# MODEL INFORMATION
# ============================================================

print("\n")
print("=" * 80)
print("MODEL INFORMATION")
print("=" * 80)

print(
    f"Model file      : {MODEL_PATH}"
)

print(
    f"Trees           : {model.num_trees()}"
)

print(
    f"Features        : {model.num_feature()}"
)

print(
    f"Objective       : "
    f"{model.params.get('objective', 'unknown')}"
)

print(
    f"Learning rate   : "
    f"{model.params.get('learning_rate', 'unknown')}"
)


# ============================================================
# INTERACTIVE MODE
# ============================================================

print("\n")
print("=" * 80)
print("INTERACTIVE V2 MODE")
print("=" * 80)

print(
    """
Enter values corresponding to the ACTUAL V2 model.

Type 'quit' at any time to exit.
"""
)


while True:

    print("\n" + "-" * 60)

    try:

        arrival = input(
            "Arrival rate — last 7 days [30]: "
        ).strip()

        if arrival.lower() in (
            "quit",
            "q",
            "exit",
        ):
            break

        arrival = float(
            arrival or "30"
        )


        queue = float(
            input(
                "Queue length at booking [4]: "
            ) or "4"
        )


        day = int(
            input(
                "Day of week (0=Mon, 6=Sun) [1]: "
            ) or "1"
        )


        month = int(
            input(
                "Month (1-12) [6]: "
            ) or "6"
        )


        day_month = int(
            input(
                "Day of month [15]: "
            ) or "15"
        )


        hour = int(
            input(
                "Appointment slot hour (0-23) [10]: "
            ) or "10"
        )


        minute = int(
            input(
                "Appointment slot minute (0-59) [0]: "
            ) or "0"
        )


        week = input(
            "ISO week of year [auto]: "
        ).strip()

        if week:

            week = int(
                week
            )

        else:

            week = None


        wait = predict_wait(

            arrival_rate_7d=
                arrival,

            queue_length_at_booking=
                queue,

            day_of_week=
                day,

            month=
                month,

            day_of_month=
                day_month,

            week_of_year=
                week,

            slot_hour=
                hour,

            slot_minute=
                minute,
        )


        pressure = (
            queue /
            max(arrival, 0.01)
        )


        print("\nPrediction")
        print("-" * 40)

        print(
            f"Arrival rate (7d) : {arrival:.2f}"
        )

        print(
            f"Queue length      : {queue:.2f}"
        )

        print(
            f"Queue pressure    : {pressure:.4f}"
        )

        print(
            f"Predicted wait    : "
            f"{wait:.2f} days"
        )


    except ValueError as exc:

        print(
            f"\nInvalid input: {exc}"
        )

    except Exception as exc:

        print(
            f"\nPrediction failed:\n{exc}"
        )


print("\n")
print("=" * 80)
print("V2 TEST COMPLETE")
print("=" * 80)