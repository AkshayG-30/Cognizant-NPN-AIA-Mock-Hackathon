"""Test the wait-time predictor end-to-end."""
import sys
sys.path.insert(0, ".")

from app.ml.model_registry import ModelRegistry
from app.ml.lightgbm_predictor import WaitTimePredictor

registry = ModelRegistry()
registry.load_wait_time_model()
predictor = WaitTimePredictor(registry)

result = predictor.predict(
    specialty="CARDIOVASCULAR DISEASE",
    arrival_rate_lambda=25.0,
    queue_length_Lq=8.0,
    utilization_rho=0.75,
    active_backlog=5,
    server_count=12,
    service_rate_mu=3.5,
    day_of_week=1,
    month=8,
    hour_of_day=10,
    org_size=200,
    offers_telehealth=0,
)
print("=== Prediction Result ===")
print(f"Predicted wait: {result['predicted_wait_days']} days")
print(f"Inference time: {result['inference_time_ms']} ms")
print(f"Model version: {result['model_version']}")
print(f"Raw prediction: {result['raw_prediction']}")
print(f"Features used: {len(result['features_used'])} features")

# Test optimizer
from app.optimization.provider_optimizer import ProviderOptimizer
import uuid

optimizer = ProviderOptimizer()
candidates = [
    {"provider_id": uuid.uuid4(), "name": "Dr. Smith", "npi": "1234567890",
     "specialty": "CARDIOVASCULAR DISEASE", "predicted_wait_days": 12.3,
     "distance_km": 5.2, "utilization_rho": 0.6, "active_backlog": 2},
    {"provider_id": uuid.uuid4(), "name": "Dr. Jones", "npi": "1234567891",
     "specialty": "CARDIOVASCULAR DISEASE", "predicted_wait_days": 8.1,
     "distance_km": 15.8, "utilization_rho": 0.85, "active_backlog": 7},
    {"provider_id": uuid.uuid4(), "name": "Dr. Patel", "npi": "1234567892",
     "specialty": "CARDIOVASCULAR DISEASE", "predicted_wait_days": 18.5,
     "distance_km": 3.1, "utilization_rho": 0.4, "active_backlog": 1},
]

opt_result = optimizer.optimize(candidates, top_k=3, target_specialty="CARDIOVASCULAR DISEASE")
print("\n=== Optimization Result ===")
print(f"Method: {opt_result['optimization_method']}")
print(f"Time: {opt_result['optimization_time_ms']} ms")
for rec in opt_result["recommendations"]:
    print(f"  Rank #{rec['rank']}: {rec['provider_name']} — score={rec['objective_score']}, wait={rec['predicted_wait_days']}d, dist={rec['distance_km']}km")
    print(f"    Reasons: {'; '.join(rec['reasons'])}")

print("\n=== ALL TESTS PASSED ===")
