import asyncio
import sys
import os
import json
import httpx

sys.path.insert(0, os.path.abspath("backend"))

from app.main import app
from app.core.config import get_settings
from app.db.database import init_db, close_db, create_tables
from app.ml.model_registry import get_model_registry

async def main():
    print("=" * 60)
    print("CarePath AI — Local Integration & Health Test")
    print("=" * 60)

    # Initialize settings, database, ML model
    settings = get_settings()
    print(f"Database URL: {settings.database_url}")
    print(f"App Environment: {settings.app_env}")
    
    init_db()
    await create_tables()
    print("Database tables verified.")

    registry = get_model_registry()
    model_loaded = registry.load_wait_time_model()
    print(f"LightGBM Wait Model Loaded: {model_loaded}")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
        # 1. Health endpoint
        r = await client.get("/api/v1/health")
        print(f"\n[1] GET /api/v1/health -> {r.status_code}")
        print("    Response:", json.dumps(r.json(), indent=2))

        # 2. Providers endpoint
        r = await client.get("/api/v1/providers?page=1&page_size=5")
        print(f"\n[2] GET /api/v1/providers?page_size=5 -> {r.status_code}")
        data = r.json()
        print(f"    Total providers in DB: {data.get('total'):,}")
        print(f"    Returned count: {len(data.get('providers', []))}")
        if data.get("providers"):
            p0 = data["providers"][0]
            print(f"    Sample Provider: {p0.get('first_name')} {p0.get('last_name')} | Specialty: {p0.get('specialty')} | City: {p0.get('city')}, {p0.get('state')}")

        # 3. Provider Search by Specialty
        r = await client.get("/api/v1/providers?specialty=CARDIOVASCULAR%20DISEASE&page_size=3")
        print(f"\n[3] GET /api/v1/providers (CARDIOVASCULAR DISEASE) -> {r.status_code}")
        data = r.json()
        print(f"    Total in Specialty: {data.get('total'):,}")

        # 4. Wait-Time Prediction API
        pred_payload = {
            "specialty": "CARDIOVASCULAR DISEASE",
            "arrival_rate_lambda": 24.5,
            "queue_length_Lq": 4.0,
            "utilization_rho": 0.72,
            "active_backlog": 3,
            "server_count": 12,
            "service_rate_mu": 3.6,
            "day_of_week": 1,
            "month": 8,
            "hour_of_day": 10,
            "org_size": 250,
            "offers_telehealth": 1
        }
        r = await client.post("/api/v1/predictions/wait-time", json=pred_payload)
        print(f"\n[4] POST /api/v1/predictions/wait-time -> {r.status_code}")
        print("    Response:", json.dumps(r.json(), indent=2))

        # 5. Create Referral
        referral_payload = {
            "patient_id": None,
            "clinical_text": "Patient presents with progressive exertional dyspnea, palpitations, and bilateral lower extremity edema. Referral requested for comprehensive cardiovascular evaluation.",
            "symptoms": ["exertional dyspnea", "palpitations", "bilateral lower extremity edema"],
            "conditions": ["congestive heart failure", "hypertension"],
            "target_specialty": "CARDIOVASCULAR DISEASE",
            "urgency": "urgent",
            "preferred_location_lat": 34.0522,
            "preferred_location_lng": -118.2437,
            "max_distance_km": 150.0,
            "insurance_network": "Blue Cross Blue Shield"
        }
        r = await client.post("/api/v1/referrals", json=referral_payload)
        print(f"\n[5] POST /api/v1/referrals -> {r.status_code}")
        ref_data = r.json()
        referral_id = ref_data.get("id")
        print(f"    Created Referral ID: {referral_id}")

        # 6. Analyze Referral
        r = await client.post(f"/api/v1/referrals/{referral_id}/analyze")
        print(f"\n[6] POST /api/v1/referrals/{referral_id}/analyze -> {r.status_code}")
        print("    Analysis:", json.dumps(r.json(), indent=2))

        # 7. Generate Recommendations (Top 3 Providers)
        rec_payload = {
            "referral_id": referral_id,
            "top_k": 3,
            "max_distance_km": 150.0,
            "weight_wait_time": 0.4,
            "weight_distance": 0.3,
            "weight_capacity": 0.2,
            "weight_fairness": 0.1
        }
        r = await client.post("/api/v1/recommendations", json=rec_payload)
        print(f"\n[7] POST /api/v1/recommendations -> {r.status_code}")
        rec_data = r.json()
        rec_id = rec_data.get("recommendation_id")
        print("    Recommendation Result:")
        print(f"    ID: {rec_id}")
        print(f"    Method: {rec_data.get('optimization_method')}")
        print(f"    Top matches count: {len(rec_data.get('recommendations', []))}")
        for rec in rec_data.get("recommendations", []):
            print(f"      Rank #{rec.get('rank')}: {rec.get('provider_name')} ({rec.get('specialty')}) - Wait: {rec.get('predicted_wait_days')} days | Distance: {rec.get('distance_km')} km | Score: {rec.get('objective_score')}")
        print("\n    Explanation:\n" + str(rec_data.get("explanation", "")))

        # 8. Explanation endpoint
        if rec_id:
            r = await client.get(f"/api/v1/recommendations/{rec_id}/explanation")
            print(f"\n[8] GET /api/v1/recommendations/{rec_id}/explanation -> {r.status_code}")
            print("    Explanation:", json.dumps(r.json(), indent=2))

    await close_db()
    print("\nAll integration test steps completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
