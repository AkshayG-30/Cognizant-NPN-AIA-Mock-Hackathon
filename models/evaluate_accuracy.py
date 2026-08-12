"""
CarePath AI — Wait-Time Model Accuracy & Classification Evaluation
Usage:
  d:\\CTS Mock\\venv\\Scripts\\python.exe d:\\CTS Mock\\models\\evaluate_accuracy.py
"""
import os
import json
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix
)
from sklearn.preprocessing import LabelEncoder

BASE = r"d:\CTS Mock"
ARTIFACTS = os.path.join(BASE, "models", "artifacts")

def get_wait_tier(days):
    """Categorize wait time in days into a clinical tier."""
    if days <= 7.0:
        return 0  # Short (<= 1 week)
    elif days <= 21.0:
        return 1  # Moderate (1-3 weeks)
    elif days <= 45.0:
        return 2  # Long (3-6 weeks)
    else:
        return 3  # Very Long (> 6 weeks)

def run_evaluation():
    print("=" * 70)
    print("CAREPATH AI — WAIT-TIME MODEL COMPREHENSIVE ACCURACY & CLASSIFICATION EVALUATION")
    print("=" * 70)

    # 1. Load Model
    model_path = os.path.join(ARTIFACTS, "wait_time_lgbm.txt")
    if not os.path.exists(model_path):
        print(f"[ERROR] Model file not found at: {model_path}")
        return
    model = lgb.Booster(model_file=model_path)
    print(f"Loaded Booster model successfully from: {model_path}")

    # 2. Load feature columns and specialty encoder
    with open(os.path.join(ARTIFACTS, "feature_columns.json")) as f:
        feature_cols = json.load(f)
    with open(os.path.join(ARTIFACTS, "specialty_encoder.json")) as f:
        spec_map = json.load(f)

    # 3. Load Dataset
    data_path = os.path.join(ARTIFACTS, "training_data.csv")
    if not os.path.exists(data_path):
        print(f"[ERROR] Dataset not found at: {data_path}")
        return
    df = pd.read_csv(data_path)
    print(f"Loaded dataset with {len(df):,} records.")

    # 4. Reconstruct features & label encoding
    le_spec = LabelEncoder()
    le_spec.classes_ = np.array([spec_map[str(i)] for i in range(len(spec_map))])
    df['specialty_encoded'] = le_spec.transform(df['specialty'])

    # Compute interaction features
    df['lambda_x_utilization'] = df['arrival_rate_lambda'] * df['utilization_rho']
    df['backlog_x_utilization'] = df['active_backlog'] * df['utilization_rho']
    df['capacity_ratio'] = df['arrival_rate_lambda'] / (df['server_count'] * df['service_rate_mu'] + 0.001)

    X = df[feature_cols].values
    y = df['wait_days'].values

    # 5. Split to get test set (same test split as training)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Re-split data. Test set size: {len(X_test):,}")

    # 6. Predict
    y_pred = model.predict(X_test)

    # 7. Regression Metrics
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / np.clip(y_test, 0.5, None))) * 100

    print("\n--- REGRESSION METRICS ---")
    print(f"  RMSE:  {rmse:.4f} days")
    print(f"  MAE:   {mae:.4f} days")
    print(f"  R2:    {r2:.5f}")
    print(f"  MAPE:  {mape:.2f}%")

    # 8. Classification Framing A: Wait-Time Tiers (Multiclass)
    # Convert actual and predicted days to categories
    v_get_tier = np.vectorize(get_wait_tier)
    y_test_tiers = v_get_tier(y_test)
    y_pred_tiers = v_get_tier(y_pred)

    tier_names = ['Short (<=7d)', 'Moderate (7-21d)', 'Long (21-45d)', 'Very Long (>45d)']
    
    # Calculate metrics
    tier_report = classification_report(y_test_tiers, y_pred_tiers, target_names=tier_names, output_dict=True)
    tier_accuracy = accuracy_score(y_test_tiers, y_pred_tiers)

    print("\n--- MULTICLASS CLASSIFICATION METRICS (WAIT-TIME TIERS) ---")
    print(f"  Overall Tier Accuracy: {tier_accuracy * 100:.2f}%")
    print(f"  {'Tier Class':<18} | {'Precision':<9} | {'Recall':<9} | {'F1-score':<9} | {'Support':<8}")
    print(f"  {'-'*63}")
    for name in tier_names:
        metrics = tier_report[name]
        print(f"  {name:<18} | {metrics['precision']*100:<8.2f}% | {metrics['recall']*100:<8.2f}% | {metrics['f1-score']*100:<8.2f}% | {int(metrics['support']):<8,}")
    
    # Macro & Weighted Averages
    macro_avg = tier_report['macro avg']
    weighted_avg = tier_report['weighted avg']
    print(f"  {'-'*63}")
    print(f"  {'Macro Average':<18} | {macro_avg['precision']*100:<8.2f}% | {macro_avg['recall']*100:<8.2f}% | {macro_avg['f1-score']*100:<8.2f}% | {int(macro_avg['support']):<8,}")
    print(f"  {'Weighted Average':<18} | {weighted_avg['precision']*100:<8.2f}% | {weighted_avg['recall']*100:<8.2f}% | {weighted_avg['f1-score']*100:<8.2f}% | {int(weighted_avg['support']):<8,}")

    # 9. Classification Framing B: Binary Classification Thresholds
    # Threshold 1: Delayed Wait (> 14 days)
    y_test_bin14 = (y_test > 14.0).astype(int)
    y_pred_bin14 = (y_pred > 14.0).astype(int)
    
    prec14, rec14, f1_14, _ = precision_recall_fscore_support(y_test_bin14, y_pred_bin14, average='binary')
    acc14 = accuracy_score(y_test_bin14, y_pred_bin14)

    # Threshold 2: Long Delay Wait (> 30 days)
    y_test_bin30 = (y_test > 30.0).astype(int)
    y_pred_bin30 = (y_pred > 30.0).astype(int)
    
    prec30, rec30, f1_30, _ = precision_recall_fscore_support(y_test_bin30, y_pred_bin30, average='binary')
    acc30 = accuracy_score(y_test_bin30, y_pred_bin30)

    print("\n--- BINARY CLASSIFICATION METRICS (DELAY ALERTS) ---")
    print(f"  Alert Threshold: Wait > 14 Days (Delayed)")
    print(f"    Accuracy:  {acc14 * 100:.2f}%")
    print(f"    Precision: {prec14 * 100:.2f}%")
    print(f"    Recall:    {rec14 * 100:.2f}%")
    print(f"    F1 Score:  {f1_14 * 100:.2f}%")
    print(f"  Alert Threshold: Wait > 30 Days (Critical Delay)")
    print(f"    Accuracy:  {acc30 * 100:.2f}%")
    print(f"    Precision: {prec30 * 100:.2f}%")
    print(f"    Recall:    {rec30 * 100:.2f}%")
    print(f"    F1 Score:  {f1_30 * 100:.2f}%")

    # 10. Specialty-wise Breakdown
    test_df = pd.DataFrame(X_test, columns=feature_cols)
    test_df['y_true'] = y_test
    test_df['y_pred'] = y_pred
    test_df['specialty'] = le_spec.inverse_transform(test_df['specialty_encoded'].astype(int))

    spec_metrics = []
    for spec in sorted(test_df['specialty'].unique()):
        mask = test_df['specialty'] == spec
        s_true = test_df.loc[mask, 'y_true']
        s_pred = test_df.loc[mask, 'y_pred']
        count = int(mask.sum())

        if count > 0:
            s_mae = mean_absolute_error(s_true, s_pred)
            s_rmse = np.sqrt(mean_squared_error(s_true, s_pred))
            s_r2 = r2_score(s_true, s_pred) if count > 1 else 0.0
            
            # Specialty classification metrics (accuracy of tier placement for this specialty)
            s_true_tiers = v_get_tier(s_true)
            s_pred_tiers = v_get_tier(s_pred)
            s_tier_acc = accuracy_score(s_true_tiers, s_pred_tiers)

            spec_metrics.append({
                'specialty': spec,
                'count': count,
                'mae': round(float(s_mae), 4),
                'rmse': round(float(s_rmse), 4),
                'r2': round(float(s_r2), 4),
                'tier_accuracy': round(float(s_tier_acc), 4)
            })

    # Save to JSON
    report_json = {
        'regression_metrics': {
            'rmse': round(rmse, 4),
            'mae': round(mae, 4),
            'r2': round(r2, 5),
            'mape': round(mape, 2)
        },
        'multiclass_tier_classification': {
            'overall_accuracy': round(float(tier_accuracy), 5),
            'report': tier_report
        },
        'binary_delayed_classification_14d': {
            'accuracy': round(float(acc14), 5),
            'precision': round(float(prec14), 5),
            'recall': round(float(rec14), 5),
            'f1_score': round(float(f1_14), 5)
        },
        'binary_delayed_classification_30d': {
            'accuracy': round(float(acc30), 5),
            'precision': round(float(prec30), 5),
            'recall': round(float(rec30), 5),
            'f1_score': round(float(f1_30), 5)
        },
        'specialty_breakdown': spec_metrics
    }

    report_json_path = os.path.join(ARTIFACTS, "evaluation_report.json")
    with open(report_json_path, 'w') as f:
        json.dump(report_json, f, indent=2)
    print(f"\nSaved updated JSON report to: {report_json_path}")

    # Generate Markdown Report
    report_md_path = os.path.join(ARTIFACTS, "evaluation_report.md")
    with open(report_md_path, 'w') as f:
        f.write("# CarePath AI — Wait-Time Prediction Accuracy & Classification Report\n\n")
        f.write("This report presents the wait-time model's performance evaluated as both a **Regression** model and a **Classification** model (by binning continuous days into clinical wait-time tiers or binary alert thresholds).\n\n")

        f.write("## 1. Regression Metrics\n")
        f.write("| Metric | Value | Description |\n")
        f.write("| :--- | :---: | :--- |\n")
        f.write(f"| **Root Mean Squared Error (RMSE)** | {rmse:.4f} days | Standard deviation of prediction errors. |\n")
        f.write(f"| **Mean Absolute Error (MAE)** | {mae:.4f} days | Average magnitude of prediction errors. |\n")
        f.write(f"| **Coefficient of Determination ($R^2$)** | {r2:.5f} | Variance in wait time explained by features. |\n")
        f.write(f"| **Mean Abs Percentage Error (MAPE)** | {mape:.2f}% | Relative prediction error in percent. |\n\n")

        f.write("## 2. Multiclass Classification: Wait-Time Tiers\n")
        f.write("To understand clinical scheduling context, continuous wait times are binned into four tiers:\n")
        f.write("- **Short**: $\\le 7$ days (1 week or less)\n")
        f.write("- **Moderate**: $7 < \\text{wait} \\le 21$ days (1 to 3 weeks)\n")
        f.write("- **Long**: $21 < \\text{wait} \\le 45$ days (3 to 6 weeks)\n")
        f.write("- **Very Long**: $> 45$ days (more than 6 weeks)\n\n")
        
        f.write(f"### **Overall Tier Placement Accuracy**: **{tier_accuracy * 100:.2f}%**\n\n")
        f.write("| Wait-Time Tier Class | Precision | Recall | F1-Score | Patients (Support) |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: |\n")
        for name in tier_names:
            m = tier_report[name]
            f.write(f"| **{name}** | {m['precision']*100:.2f}% | {m['recall']*100:.2f}% | {m['f1-score']*100:.2f}% | {int(m['support']):,} |\n")
        f.write(f"| **Macro Average** | {macro_avg['precision']*100:.2f}% | {macro_avg['recall']*100:.2f}% | {macro_avg['f1-score']*100:.2f}% | {int(macro_avg['support']):,} |\n")
        f.write(f"| **Weighted Average** | {weighted_avg['precision']*100:.2f}% | {weighted_avg['recall']*100:.2f}% | {weighted_avg['f1-score']*100:.2f}% | {int(weighted_avg['support']):,} |\n\n")

        f.write("## 3. Binary Classification: Delay Warning Alerts\n")
        f.write("In practice, the system generates automated warnings if wait times exceed standard delays (14 days) or critical delays (30 days). Below is how accurately the model flags these delays:\n\n")

        f.write("| Alert Threshold | Accuracy | Precision | Recall | F1-Score |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: |\n")
        f.write(f"| **Delayed Flag (Wait > 14 Days)** | {acc14*100:.2f}% | {prec14*100:.2f}% | {rec14*100:.2f}% | {f1_14*100:.2f}% |\n")
        f.write(f"| **Critical Delay Flag (Wait > 30 Days)** | {acc30*100:.2f}% | {prec30*100:.2f}% | {rec30*100:.2f}% | {f1_30*100:.2f}% |\n\n")

        f.write("## 4. Performance & Tier Placement Accuracy by Specialty\n")
        f.write("| Specialty | Patients (Count) | MAE (days) | RMSE (days) | $R^2$ Score | Tier Placement Accuracy |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for s in spec_metrics:
            f.write(f"| {s['specialty']} | {s['count']:,} | {s['mae']:.2f} | {s['rmse']:.2f} | {s['r2']:.4f} | {s['tier_accuracy']*100:.2f}% |\n")

        f.write("\n## 5. Evaluation Plots\n")
        f.write("The following training and validation plots have been generated and saved under `models/artifacts/`:\n")
        f.write("- **Actual vs. Predicted Scatter Plot**: `actual_vs_predicted.png`\n")
        f.write("- **Feature Importance (Gain)**: `feature_importance.png`\n")
        f.write("- **SHAP Explanations**: `shap_summary.png`\n")

    print(f"Saved updated Markdown report to: {report_md_path}")
    print("=" * 70)

if __name__ == "__main__":
    run_evaluation()
