"""Test dynamic output across 3 different specialties with model loaded."""
import asyncio
from app.db.database import init_db, get_db
from app.ml.model_registry import get_model_registry
from app.api.v1.carepath import process_carepath_workflow

# Initialize ML Model Registry
reg = get_model_registry()
reg.load_wait_time_model()
print(f"ML Wait-Time Model Loaded: {reg.is_loaded}")

async def test_case(label, text, lat=34.0522, lon=-118.2437):
    init_db("sqlite+aiosqlite:///./carepath_dev.db")
    async for db in get_db():
        res = await process_carepath_workflow(
            clinical_text=text,
            patient_lat=lat,
            patient_lon=lon,
            db=db
        )
        print(f"\n=== {label} ===")
        print(f"Detected Specialty: {res['clinical_triage']['specialty']}")
        print(f"Urgency: {res['clinical_triage']['urgency']}")
        print(f"Candidates Evaluated: {res['ml_engine']['candidates_evaluated']}")
        print(f"Avg Wait Days: {res['ml_engine']['average_predicted_wait_days']}")
        for r in res["recommendations"][:3]:
            print(
                f"  #{r['rank']} {r['name']} ({r['city']}): "
                f"quality={r['quality_score']}, "
                f"dist={r['distance_km']}km, "
                f"wait={r['predicted_wait_days']}d, "
                f"osrm={r.get('osrm_distance_km')}km, "
                f"dur={r.get('osrm_duration_minutes')}min"
            )

async def main():
    await test_case(
        "TEST 1: Cardiovascular",
        "Patient with exertional chest pressure and dyspnea. LDL 165."
    )
    await test_case(
        "TEST 2: Neurology",
        "Patient with recurrent migraines and neuropathy in left hand. MRI recommended."
    )
    await test_case(
        "TEST 3: Dermatology",
        "Persistent rash on forearm, possible eczema or dermatitis. Topical steroid ineffective."
    )

if __name__ == "__main__":
    asyncio.run(main())
