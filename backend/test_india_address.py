import asyncio
from app.db.database import init_db, get_db
from app.ml.model_registry import get_model_registry
from app.api.v1.carepath import process_carepath_workflow

reg = get_model_registry()
reg.load_wait_time_model()

async def test():
    init_db("sqlite+aiosqlite:///./carepath_dev.db")
    async for db in get_db():
        res = await process_carepath_workflow(
            clinical_text="Patient with exertional chest pressure and dyspnea.",
            patient_address="Mumbai, India",
            db=db
        )
        print("\n=== India Address Test Results ===")
        print("Specialty:", res["clinical_triage"]["specialty"])
        print("Patient Coords:", res["request_summary"]["patient_lat"], res["request_summary"]["patient_lon"])
        for r in res["recommendations"][:3]:
            print(f"Doctor: {r['name']} ({r['city']}, {r['state']})")
            print(f"  Haversine Distance: {r['distance_km']} km")
            print(f"  OSRM Road Distance: {r.get('osrm_distance_km')} km (Routing Available: {r.get('routing_available')})")
            print(f"  V4 Predicted Wait: {r['predicted_wait_days']} days\n")

if __name__ == "__main__":
    asyncio.run(test())
