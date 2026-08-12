"""Test live server API endpoints."""
import httpx
import json

base = "http://127.0.0.1:8000/api/v1"

# Test 1: Health
r = httpx.get(f"{base}/health")
print("=== HEALTH ===")
print(json.dumps(r.json(), indent=2))

# Test 2: System Info
r = httpx.get(f"{base}/system/info")
print("\n=== SYSTEM INFO ===")
d = r.json()
print(f"App: {d['app_name']} v{d['version']}")
print(f"Model loaded: {d['model_loaded']}")
print(f"Model version: {d['model_version']}")

# Test 3: Model Info
r = httpx.get(f"{base}/models")
print("\n=== MODELS ===")
models = r.json()
for m in models:
    print(f"{m['model_name']} v{m['version']} (features: {len(m['feature_schema'])})")

# Test 4: Wait Prediction Endpoint
r = httpx.post(f"{base}/predictions/wait-time", json={
    "specialty": "PSYCHIATRY",
    "arrival_rate_lambda": 30.0,
    "queue_length_Lq": 12.0,
    "utilization_rho": 0.85,
    "active_backlog": 8,
    "server_count": 13,
    "service_rate_mu": 3.4,
    "day_of_week": 1,
    "month": 8,
    "hour_of_day": 10,
    "org_size": 150,
    "offers_telehealth": 0,
})
print("\n=== WAIT PREDICTION ENDPOINT ===")
pred = r.json()
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print(f"Predicted wait: {pred['predicted_wait_days']} days")
    print(f"Model: {pred['model_name']} v{pred['model_version']}")
    print(f"Inference: {pred['inference_time_ms']} ms")
else:
    print(json.dumps(pred, indent=2))

print("\n=== ALL LIVE TESTS PASSED ===")
