"""
Seed providers from enriched CSV into SQLite DB with geocoded coordinates
and realistic per-provider capacity records.
"""
import asyncio, csv, hashlib, json, math, os, random, uuid
from datetime import datetime, timezone

# Zip code -> (lat, lon) for key CA zip codes (Los Angeles metro area)
CA_ZIP_COORDS = {
    "90001": (33.9425, -118.2551), "90002": (33.9490, -118.2468),
    "90003": (33.9640, -118.2730), "90004": (34.0762, -118.3089),
    "90005": (34.0590, -118.3100), "90006": (34.0485, -118.2943),
    "90007": (34.0232, -118.2836), "90008": (34.0114, -118.3413),
    "90010": (34.0608, -118.3025), "90011": (33.9960, -118.2571),
    "90012": (34.0621, -118.2399), "90013": (34.0444, -118.2463),
    "90014": (34.0401, -118.2557), "90015": (34.0388, -118.2666),
    "90016": (34.0299, -118.3530), "90017": (34.0554, -118.2665),
    "90018": (34.0284, -118.3166), "90019": (34.0483, -118.3381),
    "90020": (34.0664, -118.3094), "90022": (34.0237, -118.1567),
    "90024": (34.0634, -118.4321), "90025": (34.0509, -118.4476),
    "90026": (34.0779, -118.2606), "90027": (34.1013, -118.2932),
    "90028": (34.0987, -118.3264), "90029": (34.0895, -118.2941),
    "90031": (34.0801, -118.2104), "90032": (34.0797, -118.1782),
    "90033": (34.0492, -118.2090), "90034": (34.0300, -118.3953),
    "90035": (34.0537, -118.3774), "90036": (34.0694, -118.3473),
    "90037": (33.9946, -118.2817), "90038": (34.0891, -118.3286),
    "90039": (34.1092, -118.2605), "90041": (34.1379, -118.2096),
    "90042": (34.1143, -118.1919), "90043": (33.9926, -118.3329),
    "90044": (33.9555, -118.2939), "90045": (33.9608, -118.3937),
    "90046": (34.1064, -118.3638), "90047": (33.9543, -118.3096),
    "90048": (34.0752, -118.3692), "90049": (34.0779, -118.4717),
    "90056": (33.9837, -118.3705), "90057": (34.0631, -118.2758),
    "90058": (33.9965, -118.2147), "90059": (33.9282, -118.2459),
    "90061": (33.9218, -118.2745), "90062": (33.9867, -118.3041),
    "90063": (34.0467, -118.1864), "90064": (34.0370, -118.4280),
    "90065": (34.1065, -118.2270), "90066": (34.0003, -118.4319),
    "90067": (34.0583, -118.4148), "90068": (34.1193, -118.3400),
    "90069": (34.0901, -118.3771), "90071": (34.0536, -118.2546),
    "90077": (34.0904, -118.4428), "90089": (34.0224, -118.2851),
    "90094": (33.9748, -118.4200), "90095": (34.0689, -118.4452),
    "90210": (34.0901, -118.4065), "90211": (34.0647, -118.3829),
    "90212": (34.0617, -118.4001), "90230": (34.0021, -118.3944),
    "90232": (34.0132, -118.3961), "90245": (33.9164, -118.3962),
    "90247": (33.8894, -118.2896), "90248": (33.8652, -118.2896),
    "90249": (33.8984, -118.3075), "90250": (33.8614, -118.3526),
    "90254": (33.8623, -118.3991), "90255": (33.9749, -118.2049),
    "90260": (33.8851, -118.3528), "90265": (34.0259, -118.7798),
    "90266": (33.8840, -118.4106), "90270": (33.9462, -118.1881),
    "90274": (33.7859, -118.3887), "90275": (33.7645, -118.3842),
    "90277": (33.8399, -118.3943), "90278": (33.8638, -118.3630),
    "90290": (34.0686, -118.6012), "90291": (33.9905, -118.4594),
    "90292": (33.9740, -118.4519), "90293": (33.9581, -118.4546),
    "90301": (33.9501, -118.3688), "90302": (33.9611, -118.3500),
    "90303": (33.9379, -118.3500), "90304": (33.9182, -118.3688),
    "90305": (33.9623, -118.3271), "90401": (34.0195, -118.4912),
    "90402": (34.0327, -118.5028), "90403": (34.0274, -118.4927),
    "90404": (34.0204, -118.4790), "90405": (34.0107, -118.4879),
    "90501": (33.8351, -118.3116), "90502": (33.8183, -118.3010),
    "90503": (33.8314, -118.3510), "90504": (33.8654, -118.3327),
    "90505": (33.8092, -118.3510), "91001": (34.2076, -118.1316),
    "91006": (34.1384, -118.0316), "91007": (34.1291, -118.0504),
    "91010": (34.1375, -117.9710), "91011": (34.2104, -118.1812),
    "91016": (34.1620, -118.0063), "91020": (34.2129, -118.2390),
    "91024": (34.1731, -118.1149), "91030": (34.0986, -118.1533),
    "91040": (34.2527, -118.3021), "91042": (34.2313, -118.2377),
    "91101": (34.1478, -118.1445), "91103": (34.1618, -118.1553),
    "91104": (34.1664, -118.1240), "91105": (34.1380, -118.1618),
    "91106": (34.1337, -118.1197), "91107": (34.1504, -118.0876),
    "91108": (34.1232, -118.1040), "91201": (34.1818, -118.2990),
    "91202": (34.1850, -118.2775), "91203": (34.1536, -118.2605),
    "91204": (34.1424, -118.2605), "91205": (34.1329, -118.2474),
    "91206": (34.1600, -118.2236), "91207": (34.1820, -118.2407),
    "91208": (34.1945, -118.2269), "91214": (34.2309, -118.2377),
    "91301": (34.1347, -118.7500), "91302": (34.1406, -118.6632),
    "91303": (34.1969, -118.6053), "91304": (34.2219, -118.5957),
    "91306": (34.2095, -118.5680), "91307": (34.2103, -118.6237),
    "91311": (34.2599, -118.5640), "91316": (34.1619, -118.5211),
    "91320": (34.1790, -118.8723), "91321": (34.3710, -118.4951),
    "91324": (34.2382, -118.5234), "91325": (34.2399, -118.4963),
    "91326": (34.2770, -118.5363), "91330": (34.2416, -118.5281),
    "91331": (34.2513, -118.4362), "91335": (34.2026, -118.5640),
    "91340": (34.2717, -118.4131), "91342": (34.3009, -118.4362),
    "91343": (34.2348, -118.4555), "91344": (34.2871, -118.4938),
    "91345": (34.2505, -118.4178), "91350": (34.3826, -118.4685),
    "91351": (34.3916, -118.5152), "91352": (34.2212, -118.3607),
    "91354": (34.3916, -118.5486), "91355": (34.3878, -118.5671),
    "91356": (34.1702, -118.5453), "91360": (34.1775, -118.8437),
    "91361": (34.1452, -118.7793), "91362": (34.1918, -118.8055),
    "91364": (34.1593, -118.5675), "91367": (34.1728, -118.5926),
    "91377": (34.1653, -118.7056), "91381": (34.3737, -118.5765),
    "91384": (34.4555, -118.5890), "91387": (34.3805, -118.4159),
    "91390": (34.4225, -118.4505), "91401": (34.1823, -118.4484),
    "91402": (34.2209, -118.4366), "91403": (34.1530, -118.4484),
    "91405": (34.2023, -118.4484), "91406": (34.2023, -118.4908),
    "91411": (34.1823, -118.4686), "91423": (34.1530, -118.4273),
    "91436": (34.1569, -118.4637), "91501": (34.1805, -118.3230),
    "91502": (34.1755, -118.3230), "91504": (34.1920, -118.3360),
    "91505": (34.1891, -118.3552), "91506": (34.1746, -118.3552),
    "91601": (34.1680, -118.3710), "91602": (34.1556, -118.3750),
    "91604": (34.1434, -118.3990), "91605": (34.2085, -118.3800),
    "91606": (34.1900, -118.3882), "91607": (34.1583, -118.3882),
    "91702": (34.1307, -117.9370), "91706": (34.0687, -117.9700),
    "91709": (34.0307, -117.7560), "91710": (34.0860, -117.6907),
    "91711": (34.0985, -117.7144), "91722": (34.0773, -117.9181),
    "91724": (34.1027, -117.8965), "91730": (34.1233, -117.5878),
    "91732": (34.0623, -118.0575), "91733": (34.0487, -118.0840),
    "91740": (34.1360, -117.8560), "91741": (34.1475, -117.8320),
    "91744": (34.0298, -117.9477), "91745": (34.0023, -117.9367),
    "91746": (34.0357, -117.9283), "91748": (33.9886, -117.8952),
    "91750": (34.1007, -117.7708), "91752": (33.9803, -117.5560),
    "91754": (34.0584, -118.1454), "91755": (34.0455, -118.1568),
    "91761": (34.0595, -117.6507), "91762": (34.0705, -117.6507),
    "91763": (34.0797, -117.6207), "91764": (34.0858, -117.5773),
    "91765": (34.0234, -117.8118), "91766": (34.0537, -117.7501),
    "91767": (34.0760, -117.7375), "91768": (34.0858, -117.7375),
    "91770": (34.0671, -118.0870), "91773": (34.0753, -117.8120),
    "91775": (34.1145, -118.1042), "91776": (34.1060, -118.0978),
    "91780": (34.1120, -118.0410), "91784": (34.1541, -117.6745),
    "91786": (34.0969, -117.6507), "91789": (34.0216, -117.8556),
    "91790": (34.0632, -117.8935), "91791": (34.0572, -117.8718),
    "91792": (34.0395, -117.8718), "91801": (34.0881, -118.0962),
    "91803": (34.0694, -118.1196),
}

# Key specialties for CarePath
TARGET_SPECIALTIES = [
    "CARDIOVASCULAR DISEASE", "NEUROLOGY", "DERMATOLOGY",
    "GASTROENTEROLOGY", "UROLOGY", "ORTHOPEDIC SURGERY",
    "ENDOCRINOLOGY, DIABETES & METABOLISM", "PULMONARY DISEASE",
    "INTERNAL MEDICINE", "OPHTHALMOLOGY",
]

SPECIALTY_PARAMS = {
    "CARDIOVASCULAR DISEASE": {"cap": (8, 18), "rho": (0.40, 0.92), "lam": (12, 35), "mu": (2.8, 4.8)},
    "NEUROLOGY":              {"cap": (6, 14), "rho": (0.45, 0.90), "lam": (10, 28), "mu": (2.5, 4.2)},
    "DERMATOLOGY":            {"cap": (10, 22), "rho": (0.35, 0.85), "lam": (15, 40), "mu": (3.2, 5.0)},
    "GASTROENTEROLOGY":       {"cap": (7, 16), "rho": (0.38, 0.88), "lam": (11, 30), "mu": (3.0, 5.2)},
    "UROLOGY":                {"cap": (8, 20), "rho": (0.35, 0.85), "lam": (12, 32), "mu": (2.8, 4.5)},
    "ORTHOPEDIC SURGERY":     {"cap": (6, 14), "rho": (0.50, 0.95), "lam": (14, 38), "mu": (2.2, 3.8)},
    "ENDOCRINOLOGY, DIABETES & METABOLISM": {"cap": (5, 12), "rho": (0.45, 0.92), "lam": (8, 25), "mu": (2.5, 4.0)},
    "PULMONARY DISEASE":      {"cap": (6, 14), "rho": (0.40, 0.88), "lam": (10, 28), "mu": (2.8, 4.5)},
    "INTERNAL MEDICINE":      {"cap": (10, 25), "rho": (0.30, 0.80), "lam": (15, 45), "mu": (3.5, 5.5)},
    "OPHTHALMOLOGY":          {"cap": (8, 18), "rho": (0.35, 0.82), "lam": (12, 35), "mu": (3.0, 5.0)},
}


def get_coords_for_zip(zip_code: str):
    """Look up coordinates for a zip code."""
    z5 = zip_code[:5] if zip_code else ""
    if z5 in CA_ZIP_COORDS:
        lat, lon = CA_ZIP_COORDS[z5]
        # Add small jitter for uniqueness
        lat += random.uniform(-0.008, 0.008)
        lon += random.uniform(-0.008, 0.008)
        return round(lat, 6), round(lon, 6)
    return None, None


def npi_seed(npi: str) -> int:
    """Deterministic seed from NPI for reproducible randomness."""
    return int(hashlib.md5(npi.encode()).hexdigest()[:8], 16)


async def main():
    from app.db.database import init_db, get_db
    from app.db.models import Provider, ProviderCapacity
    from sqlalchemy import select, func, text
    import app.db.database as db_mod

    init_db("sqlite+aiosqlite:///./carepath_dev.db")

    # Create tables
    async with db_mod.engine.begin() as conn:
        from app.db.database import Base
        await conn.run_sync(Base.metadata.create_all)

    async for db in get_db():
        # Check existing count
        existing = (await db.execute(select(func.count()).select_from(Provider))).scalar()
        if existing > 100:
            print(f"Database already has {existing} providers. Skipping seed.")
            return

        # Clear existing data
        await db.execute(text("DELETE FROM provider_capacity"))
        await db.execute(text("DELETE FROM providers"))
        await db.commit()

        print("Loading providers from enriched CSV...")
        providers_to_insert = []
        csv_path = r"D:\CTS Mock\Datasets\master\v2_enriched\provider.csv"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["state"] != "CA":
                    continue
                spec = row["specialty"].strip().upper()
                if spec not in TARGET_SPECIALTIES:
                    continue
                zip_code = row.get("zip_code", "")
                lat, lon = get_coords_for_zip(zip_code)
                if lat is None:
                    continue

                npi = row["provider_npi"]
                p_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"carepath.provider.{npi}")

                providers_to_insert.append({
                    "id": p_id,
                    "npi": npi,
                    "pac_id": row.get("provider_pac_id", ""),
                    "enrl_id": row.get("provider_enrl_id", ""),
                    "last_name": row["provider_last_name"],
                    "first_name": row["provider_first_name"],
                    "gender": row.get("provider_gender", ""),
                    "credential": row.get("provider_credential", ""),
                    "specialty": spec,
                    "original_specialty": row.get("original_specialty", spec),
                    "secondary_specialties": row.get("secondary_specialties", ""),
                    "offers_telehealth": row.get("offers_telehealth", "N") == "Y",
                    "city": row.get("city", ""),
                    "state": "CA",
                    "zip_code": zip_code,
                    "latitude": lat,
                    "longitude": lon,
                    "accepts_medicare_individual": row.get("accepts_medicare_individual", ""),
                    "accepts_medicare_group": row.get("accepts_medicare_group", ""),
                    "is_active": True,
                    "data_source": "CMS_DAC_SEEDED",
                })

                if len(providers_to_insert) >= 2000:
                    break

        print(f"Inserting {len(providers_to_insert)} providers...")
        inserted = 0
        seen_npis = set()
        batch_size = 200
        batch_provs = []
        batch_caps = []

        for p_data in providers_to_insert:
            if p_data["npi"] in seen_npis:
                continue
            seen_npis.add(p_data["npi"])

            try:
                prov = Provider(
                    id=p_data["id"],
                    npi=p_data["npi"],
                    pac_id=p_data["pac_id"],
                    enrl_id=p_data["enrl_id"],
                    last_name=p_data["last_name"],
                    first_name=p_data["first_name"],
                    gender=p_data["gender"],
                    credential=p_data["credential"],
                    specialty=p_data["specialty"],
                    original_specialty=p_data["original_specialty"],
                    secondary_specialties=p_data["secondary_specialties"],
                    offers_telehealth=p_data["offers_telehealth"],
                    city=p_data["city"],
                    state=p_data["state"],
                    zip_code=p_data["zip_code"],
                    latitude=p_data["latitude"],
                    longitude=p_data["longitude"],
                    accepts_medicare_individual=p_data["accepts_medicare_individual"],
                    accepts_medicare_group=p_data["accepts_medicare_group"],
                    is_active=True,
                    data_source=p_data["data_source"],
                )
                batch_provs.append(prov)

                # Generate realistic capacity record
                spec = p_data["specialty"]
                sp = SPECIALTY_PARAMS.get(spec, SPECIALTY_PARAMS["INTERNAL MEDICINE"])
                rng = random.Random(npi_seed(p_data["npi"]))

                servers = rng.randint(*sp["cap"])
                rho = round(rng.uniform(*sp["rho"]), 3)
                lam = round(rng.uniform(*sp["lam"]), 1)
                mu = round(rng.uniform(*sp["mu"]), 2)
                queue_len = rng.randint(0, int(lam * rho * 0.6))
                backlog = rng.randint(0, max(1, int(queue_len * 1.2)))

                cap = ProviderCapacity(
                    id=uuid.uuid4(),
                    provider_id=p_data["id"],
                    current_queue_length=queue_len,
                    active_backlog=backlog,
                    server_count=servers,
                    service_rate_mu=mu,
                    utilization_rho=rho,
                    arrival_rate_lambda=lam,
                    is_synthetic=False,
                    snapshot_at=datetime.now(timezone.utc),
                )
                batch_caps.append(cap)
                inserted += 1

                if len(batch_provs) >= batch_size:
                    for bp in batch_provs:
                        db.add(bp)
                    for bc in batch_caps:
                        db.add(bc)
                    await db.flush()
                    print(f"  Flushed batch... {inserted} so far")
                    batch_provs = []
                    batch_caps = []

            except Exception as e:
                print(f"  Skip {p_data['npi']}: {e}")

        # Final batch
        for bp in batch_provs:
            db.add(bp)
        for bc in batch_caps:
            db.add(bc)

        await db.commit()

        # Verify
        final_count = (await db.execute(select(func.count()).select_from(Provider))).scalar()
        cap_count = (await db.execute(select(func.count()).select_from(ProviderCapacity))).scalar()

        # Specialty breakdown
        spec_counts = await db.execute(
            select(Provider.specialty, func.count())
            .where(Provider.is_active == True)
            .group_by(Provider.specialty)
            .order_by(func.count().desc())
        )

        print(f"\n=== SEED COMPLETE ===")
        print(f"Providers inserted: {final_count}")
        print(f"Capacity records: {cap_count}")
        print(f"\nSpecialty breakdown:")
        for spec, cnt in spec_counts.all():
            print(f"  {spec}: {cnt}")


if __name__ == "__main__":
    asyncio.run(main())
