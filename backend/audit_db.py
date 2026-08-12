import asyncio
from sqlalchemy import text
from app.db.database import init_db, get_engine

async def audit():
    engine = get_engine()
    async with engine.connect() as conn:
        print("=== POSTGRESQL AUDIT ===")
        print("Database connected successfully.")
        
        tables = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"))
        table_names = [t[0] for t in tables.fetchall()]
        print(f"Total tables: {len(table_names)}")
        print("Tables:", table_names)
        
        for t in table_names:
            cnt = await conn.execute(text(f'SELECT count(*) FROM "{t}"'))
            print(f"  * {t}: {cnt.scalar():,} rows")
            
        print("\n--- SAMPLE PROVIDER DATA ---")
        providers = await conn.execute(text("SELECT id, npi, first_name, last_name, specialty, city, state, zip_code, latitude, longitude, offers_telehealth FROM providers LIMIT 5"))
        for p in providers.fetchall():
            print(f"  Dr. {p[2]} {p[3]} | Specialty: {p[4]} | Loc: {p[5]}, {p[6]} {p[7]} | Geo: ({p[8]}, {p[9]}) | Telehealth: {p[10]}")
            
        print("\n--- SPECIALTIES IN DB ---")
        specialties = await conn.execute(text("SELECT specialty, count(*) FROM providers GROUP BY specialty ORDER BY count(*) DESC LIMIT 15"))
        for s in specialties.fetchall():
            print(f"  - {s[0]}: {s[1]} providers")

        print("\n--- APPOINTMENTS IN DB ---")
        appts = await conn.execute(text("SELECT count(*) FROM appointments"))
        print(f"Total appointments: {appts.scalar()}")
        
        slots = await conn.execute(text("SELECT count(*) FROM appointment_slots"))
        print(f"Total appointment slots: {slots.scalar()}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(audit())
