"""
============================================================
CAREPATH AI — WAIT-TIME MODEL V4
============================================================

V4 training pipeline.

Output directory:
    D:\\CTS Mock\\models\\artifacts\\v4

============================================================
"""

from __future__ import annotations

import json
import math
import os
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

warnings.filterwarnings("ignore")

SEED = 42
np.random.seed(SEED)


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE = Path(r"D:\CTS Mock")

DATA_DIR = (
    BASE
    / "Datasets"
    / "master"
    / "v2_enriched"
)

ARTIFACT_DIR = (
    BASE
    / "models"
    / "artifacts"
    / "v4"
)

ARTIFACT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FILE RESOLUTION
# ============================================================

def resolve_file(directory, names):
    for name in names:
        path = directory / name

        if path.exists():
            return path

    for name in names:
        matches = list(directory.rglob(name))

        if matches:
            return matches[0]

    raise FileNotFoundError(
        "Could not locate any of:\n"
        + "\n".join(
            str(directory / name)
            for name in names
        )
    )


APPOINTMENT_PATH = resolve_file(
    DATA_DIR,
    [
        "appointment.parquet",
        "appointments.parquet",
        "appointment.csv",
        "appointments.csv",
    ]
)

CAPACITY_PATH = resolve_file(
    DATA_DIR,
    [
        "capacity_slots.parquet",
        "capacity_slots.csv",
        "slots.parquet",
        "slots.csv",
    ]
)


print("=" * 80)
print("CAREPATH AI — WAIT-TIME MODEL V4")
print("=" * 80)

print(f"Appointment : {APPOINTMENT_PATH}")
print(f"Capacity    : {CAPACITY_PATH}")
print(f"Artifacts   : {ARTIFACT_DIR}")


# ============================================================
# LOAD DATA
# ============================================================

def load_data(path):
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)

    return pd.read_csv(
        path,
        low_memory=False
    )


appt = load_data(APPOINTMENT_PATH)
slots = load_data(CAPACITY_PATH)

print(
    f"\nAppointments loaded: {len(appt):,}"
)

print(
    f"Capacity slots loaded: {len(slots):,}"
)


# ============================================================
# COLUMN FINDER
# ============================================================

def find_column(df, candidates):
    lookup = {
        str(column).lower(): column
        for column in df.columns
    }

    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]

    return None


SCHED_COL = find_column(
    appt,
    [
        "scheduling_date",
        "scheduled_date",
        "booking_date",
    ]
)

APPT_COL = find_column(
    appt,
    [
        "appointment_date",
        "appt_date",
        "visit_date",
    ]
)

SLOT_DATE_COL = find_column(
    slots,
    [
        "slot_date",
        "date",
    ]
)


if SCHED_COL is None:
    raise ValueError(
        "Scheduling date column not found."
    )

if APPT_COL is None:
    raise ValueError(
        "Appointment date column not found."
    )

if SLOT_DATE_COL is None:
    raise ValueError(
        "Capacity slot date column not found."
    )


# ============================================================
# DATE CLEANING
# ============================================================

print("\nCleaning dates...")

appt[SCHED_COL] = pd.to_datetime(
    appt[SCHED_COL],
    errors="coerce"
)

appt[APPT_COL] = pd.to_datetime(
    appt[APPT_COL],
    errors="coerce"
)

slots[SLOT_DATE_COL] = pd.to_datetime(
    slots[SLOT_DATE_COL],
    errors="coerce"
)


# ============================================================
# TARGET
# ============================================================

print("Creating target...")

appt["target_wait_days"] = (
    appt[APPT_COL]
    - appt[SCHED_COL]
).dt.total_seconds() / 86400.0


appt = appt[
    appt[SCHED_COL].notna()
    & appt[APPT_COL].notna()
    & np.isfinite(
        appt["target_wait_days"]
    )
].copy()


appt = appt[
    (appt["target_wait_days"] >= 0)
    & (appt["target_wait_days"] <= 3650)
].copy()


print(
    f"Usable appointments: {len(appt):,}"
)


# ============================================================
# SORT
# ============================================================

appt = (
    appt
    .sort_values(
        [
            SCHED_COL,
            APPT_COL
        ]
    )
    .reset_index(drop=True)
)


sched_ns = (
    appt[SCHED_COL]
    .astype("int64")
    .to_numpy()
)

appt_ns = (
    appt[APPT_COL]
    .astype("int64")
    .to_numpy()
)

N = len(appt)


# ============================================================
# ARRIVAL RATE FEATURES
# ============================================================

print(
    "\nBuilding point-in-time features..."
)


def rolling_count(timestamps, window_days):
    """
    Count previous booking events inside the
    requested number of days.

    The current booking is excluded.
    """

    window_ns = (
        window_days
        * 86400
        * 10**9
    )

    left = np.searchsorted(
        timestamps,
        timestamps - window_ns,
        side="left"
    )

    right = np.arange(
        len(timestamps)
    )

    result = right - left

    return np.maximum(
        result,
        0
    )


arrival_1_count = rolling_count(
    sched_ns,
    1
)

arrival_3_count = rolling_count(
    sched_ns,
    3
)

arrival_7_count = rolling_count(
    sched_ns,
    7
)

arrival_14_count = rolling_count(
    sched_ns,
    14
)

arrival_30_count = rolling_count(
    sched_ns,
    30
)


appt["arrival_rate_1d"] = (
    arrival_1_count
)

appt["arrival_rate_3d"] = (
    arrival_3_count / 3.0
)

appt["arrival_rate_7d"] = (
    arrival_7_count / 7.0
)

appt["arrival_rate_14d"] = (
    arrival_14_count / 14.0
)

appt["arrival_rate_30d"] = (
    arrival_30_count / 30.0
)


# ============================================================
# QUEUE FEATURES
# ============================================================

print(
    "Building queue features..."
)


booking_day = (
    appt[SCHED_COL]
    .dt.normalize()
)

appointment_day = (
    appt[APPT_COL]
    .dt.normalize()
)


booking_day_int = (
    booking_day
    .to_numpy()
    .astype("datetime64[D]")
    .astype(np.int64)
)

appointment_day_int = (
    appointment_day
    .to_numpy()
    .astype("datetime64[D]")
    .astype(np.int64)
)


# ------------------------------------------------------------
# Queue length at booking
# ------------------------------------------------------------

"""
For each booking timestamp B:

An appointment belongs to the existing queue when:

    scheduling_date < B
    AND
    appointment_date > B

The implementation below performs a chronological
event sweep.
"""


# Every appointment enters the queue at its booking date.

start_events = pd.Series(
    1,
    index=booking_day_int
)


# Every appointment leaves the queue on its
# appointment date.

end_events = pd.Series(
    -1,
    index=appointment_day_int
)


start_events = (
    start_events
    .groupby(level=0)
    .sum()
)

end_events = (
    end_events
    .groupby(level=0)
    .sum()
)


events = (
    pd.concat(
        [
            start_events,
            end_events
        ],
        axis=1
    )
    .fillna(0)
)

events.columns = [
    "starts",
    "ends"
]


events["delta"] = (
    events["starts"]
    +
    events["ends"]
)


events = (
    events
    .sort_index()
)


events["active"] = (
    events["delta"]
    .cumsum()
)


event_days = (
    events.index
    .to_numpy()
)


active_values = (
    events["active"]
    .to_numpy(
        dtype=np.float64
    )
)


booking_positions = np.searchsorted(
    event_days,
    booking_day_int,
    side="left"
)


booking_positions = np.clip(
    booking_positions,
    0,
    len(active_values) - 1
)


queue_total = (
    active_values[
        booking_positions
    ]
)


appt["queue_length_at_booking"] = (
    np.maximum(
        queue_total - 1,
        0
    )
)


# ============================================================
# PENDING APPOINTMENTS
# ============================================================

"""
For the future pending queue we use the appointments
that have already been booked and whose appointment date
is still in the future.

This section performs a chronological sweep over
booking events and appointment events.
"""


# ------------------------------------------------------------
# Sort appointments by booking date
# ------------------------------------------------------------

booking_order = np.argsort(
    sched_ns,
    kind="mergesort"
)

sorted_sched = sched_ns[
    booking_order
]

sorted_appt = appt_ns[
    booking_order
]


# ------------------------------------------------------------
# Future appointment counts
# ------------------------------------------------------------

all_appointment_times = np.sort(
    appt_ns
)


def future_appointment_count(
    booking_times,
    days
):
    """
    Number of appointments whose appointment date
    lies within the requested future window.

    This is used as a capacity/demand proxy.
    """

    window_ns = (
        days
        * 86400
        * 10**9
    )

    left = np.searchsorted(
        all_appointment_times,
        booking_times,
        side="right"
    )

    right = np.searchsorted(
        all_appointment_times,
        booking_times + window_ns,
        side="right"
    )

    return (
        right - left
    ).astype(
        np.float64
    )


appt["pending_next_3d"] = (
    future_appointment_count(
        sched_ns,
        3
    )
)

appt["pending_next_7d"] = (
    future_appointment_count(
        sched_ns,
        7
    )
)

appt["pending_next_14d"] = (
    future_appointment_count(
        sched_ns,
        14
    )
)

appt["pending_next_30d"] = (
    future_appointment_count(
        sched_ns,
        30
    )
)


# ============================================================
# EARLIEST FUTURE APPOINTMENT
# ============================================================

future_position = np.searchsorted(
    all_appointment_times,
    sched_ns,
    side="right"
)


valid_future = (
    future_position
    <
    len(all_appointment_times)
)


earliest_wait = np.full(
    N,
    np.nan,
    dtype=np.float64
)


earliest_wait[valid_future] = (
    all_appointment_times[
        future_position[
            valid_future
        ]
    ]
    -
    sched_ns[
        valid_future
    ]
) / (
    86400 * 10**9
)


appt[
    "days_to_earliest_pending"
] = earliest_wait


# ============================================================
# QUEUE DENSITY
# ============================================================

appt["queue_density_3d"] = (
    appt["pending_next_3d"]
    / 3.0
)

appt["queue_density_7d"] = (
    appt["pending_next_7d"]
    / 7.0
)

appt["queue_density_14d"] = (
    appt["pending_next_14d"]
    / 14.0
)

appt["queue_density_30d"] = (
    appt["pending_next_30d"]
    / 30.0
)


# ============================================================
# QUEUE RATIOS
# ============================================================

appt["queue_to_arrival_7d"] = (
    appt["queue_length_at_booking"]
    /
    np.maximum(
        appt["arrival_rate_7d"],
        0.1
    )
)

appt["pending_7d_to_queue"] = (
    appt["pending_next_7d"]
    /
    np.maximum(
        appt["queue_length_at_booking"],
        1.0
    )
)


# ============================================================
# TEMPORAL FEATURES
# ============================================================

print(
    "Building calendar features..."
)

dt = appt[SCHED_COL]

appt["sched_year"] = (
    dt.dt.year
)

appt["sched_month"] = (
    dt.dt.month
)

appt["sched_day_of_week"] = (
    dt.dt.dayofweek
)

appt["sched_day_of_month"] = (
    dt.dt.day
)

appt["sched_quarter"] = (
    dt.dt.quarter
)

appt["sched_week_of_year"] = (
    dt.dt.isocalendar()
    .week
    .astype(float)
)

appt["sched_hour"] = (
    dt.dt.hour
)

appt["sched_minute"] = (
    dt.dt.minute
)


# ============================================================
# CYCLICAL FEATURES
# ============================================================

appt["dow_sin"] = np.sin(
    2
    * np.pi
    * appt["sched_day_of_week"]
    / 7.0
)

appt["dow_cos"] = np.cos(
    2
    * np.pi
    * appt["sched_day_of_week"]
    / 7.0
)

appt["month_sin"] = np.sin(
    2
    * np.pi
    * appt["sched_month"]
    / 12.0
)

appt["month_cos"] = np.cos(
    2
    * np.pi
    * appt["sched_month"]
    / 12.0
)


# ============================================================
# CALENDAR FLAGS
# ============================================================

appt["is_monday"] = (
    appt["sched_day_of_week"] == 0
).astype(int)

appt["is_friday"] = (
    appt["sched_day_of_week"] == 4
).astype(int)

appt["is_weekend"] = (
    appt["sched_day_of_week"] >= 5
).astype(int)

appt["is_month_start"] = (
    appt["sched_day_of_month"] <= 3
).astype(int)

appt["is_month_end"] = (
    dt.dt.is_month_end
).astype(int)

appt["is_business_hour"] = (
    (appt["sched_hour"] >= 8)
    &
    (appt["sched_hour"] <= 17)
).astype(int)


# ============================================================
# BOOKING BURST FEATURES
# ============================================================

appt["bookings_previous_24h"] = (
    arrival_1_count
)

appt["bookings_previous_72h"] = (
    arrival_3_count
)


# ============================================================
# CAPACITY FEATURES
# ============================================================

print(
    "Building planned-capacity features..."
)


capacity_dates = (
    slots[SLOT_DATE_COL]
    .dt.normalize()
    .dropna()
)


capacity_daily = (
    capacity_dates
    .value_counts()
    .sort_index()
)

capacity_daily.index = pd.to_datetime(
    capacity_daily.index
)


capacity_start = (
    capacity_daily.index.min()
)

capacity_end = (
    capacity_daily.index.max()
)


full_capacity_dates = pd.date_range(
    start=capacity_start,
    end=capacity_end,
    freq="D"
)


capacity_daily = (
    capacity_daily
    .reindex(
        full_capacity_dates,
        fill_value=0
    )
    .astype(float)
)


capacity_dates_np = (
    capacity_daily.index
    .to_numpy()
)


capacity_values = (
    capacity_daily
    .to_numpy(
        dtype=np.float64
    )
)


capacity_cumsum = np.concatenate(
    [
        np.array(
            [0.0]
        ),
        np.cumsum(
            capacity_values
        )
    ]
)


def future_capacity(
    booking_dates,
    window_days
):
    """
    Calculate total planned capacity from
    booking date through the next window_days.
    """

    booking_dates = (
    pd.to_datetime(
        booking_dates
    )
    .dt.normalize()
    .to_numpy()
)

    end_dates = (
        booking_dates
        +
        np.timedelta64(
            window_days - 1,
            "D"
        )
    )

    start_positions = np.searchsorted(
        capacity_dates_np,
        booking_dates,
        side="left"
    )

    end_positions = np.searchsorted(
        capacity_dates_np,
        end_dates,
        side="right"
    )

    start_positions = np.clip(
        start_positions,
        0,
        len(capacity_values)
    )

    end_positions = np.clip(
        end_positions,
        0,
        len(capacity_values)
    )

    return (
        capacity_cumsum[
            end_positions
        ]
        -
        capacity_cumsum[
            start_positions
        ]
    )


booking_dates = (
    appt[SCHED_COL]
    .dt.normalize()
)


appt[
    "scheduled_capacity_next_7d"
] = future_capacity(
    booking_dates,
    7
)

appt[
    "scheduled_capacity_next_14d"
] = future_capacity(
    booking_dates,
    14
)

appt[
    "scheduled_capacity_next_30d"
] = future_capacity(
    booking_dates,
    30
)


print(
    "Planned-capacity features completed."
)


# ============================================================
# DEMAND / CAPACITY RATIOS
# ============================================================

appt["demand_to_capacity_7d"] = (
    appt["pending_next_7d"]
    /
    np.maximum(
        appt[
            "scheduled_capacity_next_7d"
        ],
        1
    )
)

appt["demand_to_capacity_14d"] = (
    appt["pending_next_14d"]
    /
    np.maximum(
        appt[
            "scheduled_capacity_next_14d"
        ],
        1
    )
)

appt["demand_to_capacity_30d"] = (
    appt["pending_next_30d"]
    /
    np.maximum(
        appt[
            "scheduled_capacity_next_30d"
        ],
        1
    )
)


# ============================================================
# PATIENT FEATURES
# ============================================================

print(
    "Building patient features..."
)


dob_col = find_column(
    appt,
    [
        "dob",
        "date_of_birth",
        "birth_date",
    ]
)

sex_col = find_column(
    appt,
    [
        "sex",
        "gender",
    ]
)


if dob_col is not None:

    appt[dob_col] = pd.to_datetime(
        appt[dob_col],
        errors="coerce"
    )

    appt[
        "patient_age_at_booking"
    ] = (
        (
            appt[SCHED_COL]
            -
            appt[dob_col]
        ).dt.days
        / 365.2425
    )

    appt[
        "patient_age_at_booking"
    ] = (
        appt[
            "patient_age_at_booking"
        ]
        .clip(
            0,
            110
        )
    )

else:

    appt[
        "patient_age_at_booking"
    ] = np.nan


if sex_col is not None:

    sex_map = {
        "male": 1,
        "m": 1,
        "female": 0,
        "f": 0,
    }

    appt["sex_binary"] = (
        appt[sex_col]
        .astype(str)
        .str.lower()
        .str.strip()
        .map(sex_map)
    )

else:

    appt[
        "sex_binary"
    ] = np.nan


# ============================================================
# INSURANCE
# ============================================================

insurance_col = find_column(
    appt,
    [
        "insurance",
        "insurance_type",
        "payer",
        "coverage",
    ]
)


if insurance_col is not None:

    appt["_insurance_raw"] = (
        appt[insurance_col]
        .astype(str)
        .str.upper()
        .str.strip()
        .fillna("__MISSING__")
    )

else:

    appt[
        "_insurance_raw"
    ] = "__MISSING__"


# ============================================================
# CHRONOLOGICAL SPLIT
# ============================================================

print(
    "Creating chronological split..."
)


dates = np.sort(
    appt[
        SCHED_COL
    ]
    .dt.normalize()
    .unique()
)


d1 = dates[
    int(
        len(dates) * 0.70
    )
]

d2 = dates[
    int(
        len(dates) * 0.85
    )
]


train_mask = (
    appt[SCHED_COL]
    .dt.normalize()
    < d1
)

val_mask = (
    (appt[SCHED_COL].dt.normalize() >= d1)
    &
    (appt[SCHED_COL].dt.normalize() < d2)
)

test_mask = (
    appt[SCHED_COL]
    .dt.normalize()
    >= d2
)


train_idx = np.flatnonzero(
    train_mask
)

val_idx = np.flatnonzero(
    val_mask
)

test_idx = np.flatnonzero(
    test_mask
)


print(
    "\nTEMPORAL SPLIT"
)

print(
    f"Train: {len(train_idx):,}"
)

print(
    f"Val:   {len(val_idx):,}"
)

print(
    f"Test:  {len(test_idx):,}"
)


# ============================================================
# TRAIN-ONLY INSURANCE FREQUENCY
# ============================================================

insurance_freq = (
    appt
    .loc[
        train_idx,
        "_insurance_raw"
    ]
    .value_counts(
        normalize=True
    )
    .to_dict()
)


appt["insurance_frequency"] = (
    appt["_insurance_raw"]
    .map(
        insurance_freq
    )
    .fillna(0.0)
)


# ============================================================
# FEATURES
# ============================================================

FEATURES = [

    "arrival_rate_1d",
    "arrival_rate_3d",
    "arrival_rate_7d",
    "arrival_rate_14d",
    "arrival_rate_30d",

    "bookings_previous_24h",
    "bookings_previous_72h",

    "queue_length_at_booking",

    "pending_next_3d",
    "pending_next_7d",
    "pending_next_14d",
    "pending_next_30d",

    "queue_density_3d",
    "queue_density_7d",
    "queue_density_14d",
    "queue_density_30d",

    "days_to_earliest_pending",

    "queue_to_arrival_7d",
    "pending_7d_to_queue",

    "scheduled_capacity_next_7d",
    "scheduled_capacity_next_14d",
    "scheduled_capacity_next_30d",

    "demand_to_capacity_7d",
    "demand_to_capacity_14d",
    "demand_to_capacity_30d",

    "sched_year",
    "sched_month",
    "sched_day_of_week",
    "sched_day_of_month",
    "sched_quarter",
    "sched_week_of_year",
    "sched_hour",
    "sched_minute",

    "dow_sin",
    "dow_cos",
    "month_sin",
    "month_cos",

    "is_monday",
    "is_friday",
    "is_weekend",
    "is_month_start",
    "is_month_end",
    "is_business_hour",

    "patient_age_at_booking",
    "sex_binary",

    "insurance_frequency",
]


FEATURES = [
    feature
    for feature in FEATURES
    if feature in appt.columns
]


# ============================================================
# LEAKAGE AUDIT
# ============================================================

print(
    "\nRunning leakage audit..."
)


FORBIDDEN = [

    "target_wait_days",
    "wait_days",

    "appointment_status",
    "status",
    "visit_status",
    "attendance_status",

    "appointment_duration",
    "duration",

    "check_in_time",
    "start_time",
    "end_time",

    "actual_start_time",
    "actual_end_time",

    "service_rate_30d",
    "utilization_derived",

    "is_available",
]


forbidden_used = (
    set(FEATURES)
    & set(FORBIDDEN)
)


if forbidden_used:
    raise RuntimeError(
        "LEAKAGE FEATURES FOUND:\n"
        + "\n".join(
            forbidden_used
        )
    )


print(
    "Leakage audit: PASSED"
)


# ============================================================
# TRAIN-ONLY IMPUTATION
# ============================================================

print(
    "Applying train-only imputation..."
)


imputation = {}


for feature in FEATURES:

    train_values = pd.to_numeric(
        appt.loc[
            train_idx,
            feature
        ],
        errors="coerce"
    )

    median = (
        train_values
        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )
        .median()
    )

    if pd.isna(median):
        median = 0.0

    imputation[
        feature
    ] = float(median)

    appt[feature] = (
        pd.to_numeric(
            appt[feature],
            errors="coerce"
        )
        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )
        .fillna(median)
    )


# ============================================================
# REMOVE CONSTANT FEATURES
# ============================================================

usable_features = []


for feature in FEATURES:

    unique_count = (
        appt
        .loc[
            train_idx,
            feature
        ]
        .nunique()
    )

    if unique_count > 1:
        usable_features.append(
            feature
        )


FEATURES = usable_features


# ============================================================
# REMOVE HIGHLY REDUNDANT FEATURES
# ============================================================

print(
    "Checking feature redundancy..."
)


if len(FEATURES) > 1:

    corr = (
        appt
        .loc[
            train_idx,
            FEATURES
        ]
        .corr()
        .abs()
    )

else:

    corr = pd.DataFrame()


y_train_raw = (
    appt
    .loc[
        train_idx,
        "target_wait_days"
    ]
    .to_numpy()
)


target_corr = {}


for feature in FEATURES:

    values = (
        appt
        .loc[
            train_idx,
            feature
        ]
        .to_numpy()
    )

    if (
        np.std(values) > 0
        and np.std(y_train_raw) > 0
    ):

        target_corr[feature] = abs(
            np.corrcoef(
                values,
                y_train_raw
            )[0, 1]
        )

    else:

        target_corr[feature] = 0.0


remove = set()


for i, feature_a in enumerate(
    FEATURES
):

    for feature_b in FEATURES[
        i + 1:
    ]:

        if (
            corr.loc[
                feature_a,
                feature_b
            ]
            >= 0.98
        ):

            if (
                target_corr[feature_a]
                <
                target_corr[feature_b]
            ):

                remove.add(
                    feature_a
                )

            else:

                remove.add(
                    feature_b
                )


FEATURES = [
    feature
    for feature in FEATURES
    if feature not in remove
]


print(
    "\nFINAL FEATURES"
)

for index, feature in enumerate(
    FEATURES,
    1
):

    print(
        f"{index:02d}. {feature}"
    )


print(
    f"\nFinal feature count: "
    f"{len(FEATURES)}"
)


# ============================================================
# MATRICES
# ============================================================

print(
    "\nCreating training matrices..."
)


X = (
    appt[
        FEATURES
    ]
    .astype(
        np.float32
    )
)

y = (
    appt[
        "target_wait_days"
    ]
    .astype(
        np.float32
    )
)


X_train = X.iloc[
    train_idx
]

X_val = X.iloc[
    val_idx
]

X_test = X.iloc[
    test_idx
]

y_train = y.iloc[
    train_idx
]

y_val = y.iloc[
    val_idx
]

y_test = y.iloc[
    test_idx
]


# ============================================================
# LIGHTGBM DATASETS
# ============================================================

train_set = lgb.Dataset(
    X_train,
    label=y_train,
    feature_name=FEATURES,
    free_raw_data=False
)

val_set = lgb.Dataset(
    X_val,
    label=y_val,
    reference=train_set,
    feature_name=FEATURES,
    free_raw_data=False
)


# ============================================================
# LIGHTGBM PARAMETERS
# ============================================================

PARAMS = {

    "objective": "regression_l1",

    "metric": [
        "l1",
        "rmse",
    ],

    "boosting_type": "gbdt",

    "learning_rate": 0.015,

    "num_leaves": 31,

    "max_depth": 8,

    "min_data_in_leaf": 80,

    "lambda_l1": 0.10,

    "lambda_l2": 2.0,

    "feature_fraction": 0.75,

    "bagging_fraction": 0.80,

    "bagging_freq": 1,

    "feature_fraction_seed": SEED,

    "bagging_seed": SEED,

    "data_random_seed": SEED,

    "extra_trees": True,

    "extra_seed": SEED,

    "verbosity": -1,

    "num_threads": max(
        1,
        (os.cpu_count() or 4) - 1
    ),

    "seed": SEED,
}


# ============================================================
# TRAIN
# ============================================================

print(
    "\n"
    + "=" * 80
)

print(
    "TRAINING CAREPATH WAIT-TIME V4"
)

print(
    "=" * 80
)

print(
    "Maximum trees    : 4000"
)

print(
    "Learning rate    : 0.015"
)

print(
    "Feature fraction : 0.75"
)

print(
    "Bagging fraction : 0.80"
)

print(
    "Extra trees      : TRUE"
)

print(
    f"Training rows    : {len(X_train):,}"
)

print(
    f"Validation rows  : {len(X_val):,}"
)

print(
    f"Test rows        : {len(X_test):,}"
)

print(
    "=" * 80
)


start = time.time()


model = lgb.train(
    PARAMS,
    train_set,
    num_boost_round=4000,
    valid_sets=[
        train_set,
        val_set
    ],
    valid_names=[
        "train",
        "validation"
    ],
    callbacks=[
        lgb.log_evaluation(100),
        lgb.early_stopping(
            500,
            first_metric_only=True
        )
    ]
)


elapsed = (
    time.time() - start
)


print(
    f"\nTraining time: "
    f"{elapsed:.2f} seconds"
)

print(
    f"Trees trained: "
    f"{model.num_trees()}"
)

print(
    f"Best iteration: "
    f"{model.best_iteration}"
)


# ============================================================
# PREDICTIONS
# ============================================================

print(
    "\nGenerating predictions..."
)


pred_train = model.predict(
    X_train
)

pred_val = model.predict(
    X_val
)

pred_test = model.predict(
    X_test
)


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    actual,
    predicted
):

    mae = mean_absolute_error(
        actual,
        predicted
    )

    rmse = math.sqrt(
        mean_squared_error(
            actual,
            predicted
        )
    )

    r2 = r2_score(
        actual,
        predicted
    )

    within_1 = (
        np.mean(
            np.abs(
                actual - predicted
            ) <= 1
        )
        * 100
    )

    within_3 = (
        np.mean(
            np.abs(
                actual - predicted
            ) <= 3
        )
        * 100
    )

    return {
        "MAE_days": float(mae),
        "RMSE_days": float(rmse),
        "R2": float(r2),
        "within_1_day_percent": float(
            within_1
        ),
        "within_3_days_percent": float(
            within_3
        ),
    }


train_metrics = calculate_metrics(
    y_train,
    pred_train
)

val_metrics = calculate_metrics(
    y_val,
    pred_val
)

test_metrics = calculate_metrics(
    y_test,
    pred_test
)


# ============================================================
# BASELINES
# ============================================================

median_prediction = np.full(
    len(y_test),
    y_train.median()
)

mean_prediction = np.full(
    len(y_test),
    y_train.mean()
)


median_metrics = calculate_metrics(
    y_test,
    median_prediction
)

mean_metrics = calculate_metrics(
    y_test,
    mean_prediction
)


# ============================================================
# RESULTS
# ============================================================

print(
    "\n"
    + "=" * 80
)

print(
    "CAREPATH AI — V4 RESULTS"
)

print(
    "=" * 80
)

print("\nTRAIN")

print(
    f"MAE       : "
    f"{train_metrics['MAE_days']:.4f}"
)

print(
    f"RMSE      : "
    f"{train_metrics['RMSE_days']:.4f}"
)

print(
    f"R²        : "
    f"{train_metrics['R2']:.4f}"
)


print("\nVALIDATION")

print(
    f"MAE       : "
    f"{val_metrics['MAE_days']:.4f}"
)

print(
    f"RMSE      : "
    f"{val_metrics['RMSE_days']:.4f}"
)

print(
    f"R²        : "
    f"{val_metrics['R2']:.4f}"
)


print("\nTEST")

print(
    f"MAE       : "
    f"{test_metrics['MAE_days']:.4f}"
)

print(
    f"RMSE      : "
    f"{test_metrics['RMSE_days']:.4f}"
)

print(
    f"R²        : "
    f"{test_metrics['R2']:.4f}"
)

print(
    f"Within ±1d: "
    f"{test_metrics['within_1_day_percent']:.2f}%"
)

print(
    f"Within ±3d: "
    f"{test_metrics['within_3_days_percent']:.2f}%"
)


print("\nMEDIAN BASELINE")

print(
    f"MAE       : "
    f"{median_metrics['MAE_days']:.4f}"
)

print(
    f"RMSE      : "
    f"{median_metrics['RMSE_days']:.4f}"
)

print(
    f"R²        : "
    f"{median_metrics['R2']:.4f}"
)


print("\nMEAN BASELINE")

print(
    f"MAE       : "
    f"{mean_metrics['MAE_days']:.4f}"
)

print(
    f"RMSE      : "
    f"{mean_metrics['RMSE_days']:.4f}"
)

print(
    f"R²        : "
    f"{mean_metrics['R2']:.4f}"
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print(
    "\nCalculating feature importance..."
)


gain = model.feature_importance(
    importance_type="gain"
)

split = model.feature_importance(
    importance_type="split"
)


importance = pd.DataFrame({
    "feature": FEATURES,
    "gain": gain,
    "split": split,
})


importance = (
    importance
    .sort_values(
        "gain",
        ascending=False
    )
    .reset_index(
        drop=True
    )
)


print(
    "\n"
    + "=" * 80
)

print(
    "FEATURE IMPORTANCE"
)

print(
    "=" * 80
)

print(
    importance.to_string(
        index=False
    )
)


# ============================================================
# TEST PREDICTIONS
# ============================================================

print(
    "\nSaving test predictions..."
)


test_predictions = pd.DataFrame({
    "scheduling_date":
        appt.iloc[
            test_idx
        ][SCHED_COL].values,

    "appointment_date":
        appt.iloc[
            test_idx
        ][APPT_COL].values,

    "actual_wait_days":
        y_test.values,

    "predicted_wait_days":
        pred_test,
})


test_predictions[
    "absolute_error_days"
] = np.abs(
    test_predictions[
        "actual_wait_days"
    ]
    -
    test_predictions[
        "predicted_wait_days"
    ]
)


test_predictions.to_csv(
    ARTIFACT_DIR
    / "v4_test_predictions.csv",
    index=False
)


# ============================================================
# SAVE MODEL
# ============================================================

print(
    "\nSaving model..."
)


model.save_model(
    str(
        ARTIFACT_DIR
        / "wait_time_lgbm_v4.lgb"
    )
)

model.save_model(
    str(
        ARTIFACT_DIR
        / "wait_time_lgbm_v4.txt"
    )
)


# ============================================================
# SAVE FEATURE IMPORTANCE
# ============================================================

importance.to_csv(
    ARTIFACT_DIR
    / "v4_feature_importance.csv",
    index=False
)


# ============================================================
# SAVE METRICS
# ============================================================

metrics_output = {
    "model_version": "V4",

    "target":
        "appointment_date - scheduling_date",

    "target_semantics":
        "booking lead time",

    "dataset_rows":
        int(len(appt)),

    "train_rows":
        int(len(train_idx)),

    "validation_rows":
        int(len(val_idx)),

    "test_rows":
        int(len(test_idx)),

    "features":
        FEATURES,

    "feature_count":
        len(FEATURES),

    "trees":
        int(model.num_trees()),

    "best_iteration":
        int(model.best_iteration),

    "training_seconds":
        float(elapsed),

    "parameters":
        PARAMS,

    "train":
        train_metrics,

    "validation":
        val_metrics,

    "test":
        test_metrics,

    "median_baseline":
        median_metrics,

    "mean_baseline":
        mean_metrics,
}


with open(
    ARTIFACT_DIR
    / "v4_metrics.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metrics_output,
        f,
        indent=2
    )


# ============================================================
# SAVE FEATURE MANIFEST
# ============================================================

manifest = {
    "model":
        "CarePath AI Wait-Time V4",

    "target":
        "appointment_date - scheduling_date",

    "target_semantics":
        "booking lead time",

    "features":
        FEATURES,

    "feature_count":
        len(FEATURES),

    "trees":
        int(model.num_trees()),

    "best_iteration":
        int(model.best_iteration),

    "learning_rate":
        PARAMS[
            "learning_rate"
        ],

    "feature_fraction":
        PARAMS[
            "feature_fraction"
        ],

    "bagging_fraction":
        PARAMS[
            "bagging_fraction"
        ],

    "bagging_freq":
        PARAMS[
            "bagging_freq"
        ],

    "extra_trees":
        PARAMS[
            "extra_trees"
        ],

    "leakage_policy": {
        "uses_appointment_date_as_feature":
            False,

        "uses_status":
            False,

        "uses_duration":
            False,

        "uses_final_slot_availability":
            False,

        "uses_service_rate":
            False,

        "uses_utilization":
            False,

        "uses_provider":
            False,

        "uses_specialty":
            False,
    },
}


with open(
    ARTIFACT_DIR
    / "v4_feature_manifest.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        manifest,
        f,
        indent=2
    )


# ============================================================
# FINAL
# ============================================================

print(
    "\n"
    + "=" * 80
)

print(
    "CAREPATH AI — V4 TRAINING COMPLETE"
)

print(
    "=" * 80
)

print(
    f"Model: "
    f"{ARTIFACT_DIR / 'wait_time_lgbm_v4.lgb'}"
)

print(
    f"Text model: "
    f"{ARTIFACT_DIR / 'wait_time_lgbm_v4.txt'}"
)

print(
    f"Features: "
    f"{len(FEATURES)}"
)

print(
    f"Trees: "
    f"{model.num_trees()}"
)

print(
    f"Best iteration: "
    f"{model.best_iteration}"
)

print(
    f"Test MAE: "
    f"{test_metrics['MAE_days']:.4f} days"
)

print(
    f"Test RMSE: "
    f"{test_metrics['RMSE_days']:.4f} days"
)

print(
    f"Test R²: "
    f"{test_metrics['R2']:.4f}"
)

print(
    f"Within ±1 day: "
    f"{test_metrics['within_1_day_percent']:.2f}%"
)

print(
    f"Within ±3 days: "
    f"{test_metrics['within_3_days_percent']:.2f}%"
)

print(
    "\nArtifacts:"
)

for path in sorted(
    ARTIFACT_DIR.iterdir()
):
    print(
        f"  {path.name}"
    )

print(
    "\n"
    + "=" * 80
)