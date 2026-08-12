import asyncio
from sqlalchemy import text
from app.db.database import get_engine

async def inspect_providers():
    engine = get_engine()
    async with engine.connect() as conn:
        print("=== PROVIDER GEO & CONTACT INSPECTION ===")
        # Count providers with lat/lng
        geo_cnt = await conn.execute(text("SELECT count(*) FROM providers WHERE latitude IS NOT NULL AND longitude IS NOT NULL"))
        print(f"Providers with coordinates: {geo_cnt.scalar():,} / 3,136,233")
        
        # Check provider columns
        cols = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'providers'"))
        print("\nProvider columns:")
        for c in cols.fetchall():
            print(f"  - {c[0]} ({c[1]})")
            
        # Sample with lat/lng
        sample_geo = await conn.execute(text("SELECT id, first_name, last_name, specialty, city, state, zip_code, latitude, longitude, pac_id FROM providers WHERE latitude IS NOT NULL LIMIT 5"))
        print("\nSample providers with geo:")
        for p in sample_geo.fetchall():
            print(f"  Dr. {p[1]} {p[2]} | {p[3]} | {p[4]}, {p[5]} {p[6]} | ({p[7]}, {p[8]}) | PAC: {p[9]}")
            
        # Check how facilities/organizations are linked
        org_cnt = await conn.execute(text("SELECT count(*) FROM organizations"))
        print(f"\nOrganizations count: {org_cnt.scalar()}")
        
        # Check appointments table columns
        appt_cols = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'appointments'"))
        print("\nAppointments columns:")
        for c in appt_cols.fetchall():
            print(f"  - {c[0]} ({c[1]})")
            
        sample_appts = await conn.execute(text("SELECT id, provider_id, scheduled_date, scheduled_time, status, notes FROM appointments LIMIT 5"))
        print("\nSample appointments:")
        for a in sample_appts.fetchall():
            print(f"  ID: {a[0]} | Provider: {a[1]} | Date: {a[2]} {a[3]} | Status: {a[4]} | Notes: {a[5]}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(inspect_providers())
