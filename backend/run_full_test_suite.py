"""
CarePath AI — Full Backend Test Suite
Executes end-to-end testing across all key API components, LightGBM inference,
OR-Tools optimization, and FHIR translation.
"""
import sys
import json
import uuid
import httpx
from datetime import datetime, timezone

# Ensure backend root is in import path
sys.path.insert(0, ".")

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_live_server_endpoints():
    """Test all key live server endpoints running on http://127.0.0.1:8000."""
    base_url = "http://127.0.0.1:8000/api/v1"
    
    print_section("1. Testing Health & System Endpoints")
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        # Health check
        res = client.get("/health")
        print(f"[GET /health] Status: {res.status_code}")
        print("Response:", json.dumps(res.json(), indent=2))
        assert res.status_code == 200, "Health check failed"
        
        # System info
        res = client.get("/system/info")
        print(f"\n[GET /system/info] Status: {res.status_code}")
        data = res.json()
        print(f"App: {data['app_name']} v{data['version']} (Env: {data['environment']})")
        print(f"Model Loaded: {data['model_loaded']} (Version: {data['model_version']})")
        assert res.status_code == 200, "System info failed"

    print_section("2. Testing Model Registry & Wait-Time Prediction API")
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        # List models
        res = client.get("/models")
        print(f"[GET /models] Status: {res.status_code}")
        models = res.json()
        print(f"Available Models: {len(models)}")
        for m in models:
            r2_val = m['metrics'].get('r2')
            print(f"  - {m['model_name']} v{m['version']} | R^2: {r2_val} | Features: {len(m['feature_schema'])}")

        # Wait-Time Prediction API Test
        payload = {
            "specialty": "CARDIOVASCULAR DISEASE",
            "arrival_rate_lambda": 28.5,
            "queue_length_Lq": 9.2,
            "utilization_rho": 0.81,
            "active_backlog": 6,
            "server_count": 14,
            "service_rate_mu": 3.8,
            "day_of_week": 2,
            "month": 8,
            "hour_of_day": 14,
            "org_size": 250,
            "offers_telehealth": 1
        }
        res = client.post("/predictions/wait-time", json=payload)
        print(f"\n[POST /predictions/wait-time] Status: {res.status_code}")
        pred_data = res.json()
        print(f"Predicted Wait Time: {pred_data['predicted_wait_days']} days")
        print(f"Model Engine: {pred_data['model_name']} ({pred_data['model_version']})")
        print(f"Inference Duration: {pred_data['inference_time_ms']} ms")
        assert res.status_code == 200, "Prediction failed"

    print_section("3. Testing Local Optimization Engine & Strategy")
    from app.optimization.provider_optimizer import ProviderOptimizer
    optimizer = ProviderOptimizer(
        weight_wait_time=0.4,
        weight_distance=0.3,
        weight_capacity=0.2,
        weight_fairness=0.1
    )
    
    provider_candidates = [
        {
            "provider_id": uuid.uuid4(),
            "provider_name": "Dr. Sarah Jenkins",
            "npi": "1982736450",
            "specialty": "CARDIOVASCULAR DISEASE",
            "predicted_wait_days": 4.5,
            "distance_km": 12.4,
            "utilization_rho": 0.65,
            "active_backlog": 3
        },
        {
            "provider_id": uuid.uuid4(),
            "provider_name": "Dr. Robert Chen",
            "npi": "1209384756",
            "specialty": "CARDIOVASCULAR DISEASE",
            "predicted_wait_days": 14.2,
            "distance_km": 3.1,
            "utilization_rho": 0.45,
            "active_backlog": 1
        },
        {
            "provider_id": uuid.uuid4(),
            "provider_name": "Metro Heart Institute",
            "npi": "1546372819",
            "specialty": "CARDIOVASCULAR DISEASE",
            "predicted_wait_days": 8.0,
            "distance_km": 8.5,
            "utilization_rho": 0.88,
            "active_backlog": 12
        }
    ]
    
    opt_res = optimizer.optimize(provider_candidates, top_k=3, target_specialty="CARDIOVASCULAR DISEASE")
    print(f"Optimization Method Used: {opt_res['optimization_method']}")
    print(f"Execution Speed: {opt_res['optimization_time_ms']} ms")
    print("Ranked Provider Output:")
    for rec in opt_res["recommendations"]:
        p_name = rec.get('provider_name') or "Provider"
        print(f"  Rank #{rec['rank']}: {p_name} (Objective Score: {rec['objective_score']})")
        print(f"    - Wait: {rec['predicted_wait_days']}d | Distance: {rec['distance_km']}km")
        print(f"    - Rationale: {'; '.join(rec['reasons'])}")

    print_section("4. Testing FHIR R4 ServiceRequest Converter")
    from app.fhir.mapper import FHIRMapper
    from app.db.models import Referral, UrgencyLevel, ReferralStatus
    
    dummy_referral = Referral(
        id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        clinical_text="54yo M with persistent angina and elevated troponin levels.",
        symptoms=["chest pain", "shortness of breath"],
        conditions=["hypertension", "hyperlipidemia"],
        target_specialty="CARDIOVASCULAR DISEASE",
        inferred_specialty="CARDIOVASCULAR DISEASE",
        urgency=UrgencyLevel.URGENT,
        status=ReferralStatus.SUBMITTED,
        referring_provider_npi="1992883771",
        max_distance_km=25.0,
        insurance_network="BCBS PPO"
    )
    
    fhir_resource = FHIRMapper.referral_to_service_request(dummy_referral)
    print("Generated FHIR R4 Resource Type:", fhir_resource.get("resourceType"))
    print("FHIR Status:", fhir_resource.get("status"))
    print("FHIR Priority:", fhir_resource.get("priority"))
    print("Category Display:", fhir_resource.get("category", [{}])[0].get("text"))
    print("Reason Codes:", [r.get("text") for r in fhir_resource.get("reasonCode", [])])

    print_section("SUCCESS: ALL BACKEND SUITE TESTS EXECUTED SUCCESSFULLY")

if __name__ == "__main__":
    test_live_server_endpoints()
