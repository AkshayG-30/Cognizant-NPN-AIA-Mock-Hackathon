"""
CarePath AI — End-to-End System & API Verification Test Suite
"""
import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"


async def run_tests():
    print("==================================================")
    print(" CarePath AI End-to-End Full System Verification")
    print("==================================================")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health check
        print("\n1. Testing Health Endpoint...")
        r = await client.get(f"{BASE_URL}/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        data = r.json()
        print(f"   [+] Health Status: {data['status']}, Database: {data['database']}, Model Available: {data['model_available']}")

        # 2. Auth Login
        print("\n2. Testing Auth Login...")
        r = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "patient@carepath.ai", "password": "password123"},
        )
        assert r.status_code == 200, f"Auth login failed: {r.text}"
        auth_data = r.json()
        token = auth_data["token"]
        user = auth_data["user"]
        print(f"   [+] Authenticated as: {user['name']} ({user['role']})")
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Auth Me
        print("\n3. Testing Auth /me...")
        r = await client.get(f"{BASE_URL}/auth/me", headers=headers)
        assert r.status_code == 200
        print(f"   [+] /auth/me verified: {r.json()['email']}")

        # 4. Specialties
        print("\n4. Testing Specialties...")
        r = await client.get(f"{BASE_URL}/specialties")
        assert r.status_code == 200
        specs = r.json()
        print(f"   [+] Found {len(specs)} canonical specialties. Examples: {specs[:3]}")

        # 5. Doctors Directory
        print("\n5. Testing Doctors Directory...")
        r = await client.get(f"{BASE_URL}/doctors?specialty=CARDIOVASCULAR%20DISEASE")
        assert r.status_code == 200
        docs = r.json()
        print(f"   [+] Retrieved {len(docs)} cardiovascular specialists")
        doc_id = docs[0]["id"] if docs else None
        if docs:
            print(f"   [+] Top doctor: {docs[0]['name']} at {docs[0]['hospital']} (Wait: {docs[0]['wait_days']}d)")

        # 6. Doctor Profile
        if doc_id:
            print(f"\n6. Testing Doctor Profile for ID {doc_id}...")
            r = await client.get(f"{BASE_URL}/doctors/{doc_id}")
            assert r.status_code == 200
            print(f"   [+] Doctor profile: {r.json()['name']} - {r.json()['specialty']}")

        # 7. Hospitals
        print("\n7. Testing Hospitals / Facilities...")
        r = await client.get(f"{BASE_URL}/hospitals")
        assert r.status_code == 200
        hosps = r.json()
        print(f"   [+] Retrieved {len(hosps)} healthcare facilities")

        # 8. Reports & Uploads
        print("\n8. Testing Patient Reports...")
        r = await client.get(f"{BASE_URL}/reports/mine", headers=headers)
        assert r.status_code == 200
        reports = r.json()
        print(f"   [+] Patient has {len(reports)} uploaded reports")

        # 9. AI Analysis
        print("\n9. Testing AI Clinical Analysis...")
        r = await client.post(
            f"{BASE_URL}/ai/analyze",
            json={"clinical_text": "Patient has elevated LDL 151 mg/dL, Total Cholesterol 228 mg/dL, exertional dyspnea."},
        )
        assert r.status_code == 200
        ai_res = r.json()
        print(f"   [+] AI Inferred Specialty: {ai_res['specialty']} (Confidence: {ai_res['confidence']}%, Urgency: {ai_res['priority']})")
        print(f"   [+] Clinical Reasoning: {ai_res['reasoning'][:100]}...")

        # 10. CarePath Best Match (LightGBM + OR-Tools ranking)
        print("\n10. Testing CarePath Best Match Recommendation...")
        r = await client.get(f"{BASE_URL}/carepath/best-match")
        assert r.status_code == 200
        match = r.json()
        assert not match.get("empty"), "Best match should return top recommended provider"
        print(f"   [+] Best Match Doctor: {match['doctor']['name']}")
        print(f"   [+] Predicted Wait Time: {match['doctor']['wait_days']} days | Quality: {match['doctor']['quality']}/100")
        print(f"   [+] Match Reasons: {match['reasons']}")

        # 11. Patient Referral Creation
        print("\n11. Testing Referral Submission...")
        ref_payload = {
            "reason": "Cardiology referral for lipid management and chest tightness",
            "symptoms": "Dyspnea on exertion, fatigue, family history of CAD",
            "duration": "4 weeks",
            "urgency": "routine",
            "target_specialty": "CARDIOVASCULAR DISEASE",
        }
        r = await client.post(f"{BASE_URL}/referrals", json=ref_payload, headers=headers)
        assert r.status_code == 201
        created_ref = r.json()
        print(f"   [+] Referral created: ID={created_ref['id']}, Reason='{created_ref['reason']}'")

        # 12. Latest Referral
        print("\n12. Testing Referral /mine/latest...")
        r = await client.get(f"{BASE_URL}/referrals/mine/latest", headers=headers)
        assert r.status_code == 200
        latest = r.json()
        print(f"   [+] Latest referral retrieved: {latest['reason']} (Specialty: {latest['suggested_specialty']})")

        # 13. Appointments (Create & List)
        print("\n13. Testing Appointment Booking & Retrieval...")
        appt_payload = {
            "doctor_id": doc_id or "00000000-0000-0000-0000-000000000000",
            "date": "2026-08-22",
            "time": "10:00 AM",
            "reason": "Consultation",
        }
        r = await client.post(f"{BASE_URL}/appointments", json=appt_payload, headers=headers)
        assert r.status_code == 201
        new_appt = r.json()
        print(f"   [+] Appointment Booked: ID={new_appt['id']} with {new_appt['doctor_name']} on {new_appt['date']} at {new_appt['time']}")

        r = await client.get(f"{BASE_URL}/appointments?scope=upcoming", headers=headers)
        assert r.status_code == 200
        appts = r.json()
        print(f"   [+] Retrieved {len(appts)} upcoming appointments")

        # 14. Notifications
        print("\n14. Testing Notifications...")
        r = await client.get(f"{BASE_URL}/notifications")
        assert r.status_code == 200
        notifs = r.json()
        print(f"   [+] Retrieved {len(notifs)} system notifications")

        # 15. Messages
        print("\n15. Testing Messages...")
        r = await client.get(f"{BASE_URL}/messages")
        assert r.status_code == 200
        msgs = r.json()
        print(f"   [+] Retrieved {len(msgs)} clinical messages")

        # 16. Admin Operations & Analytics
        print("\n16. Testing Admin Stats & Operations...")
        r = await client.get(f"{BASE_URL}/admin/stats")
        assert r.status_code == 200
        stats = r.json()
        print(f"   [+] Platform Stats: Doctors={stats['doctors']}, Patients={stats['patients']}, Referrals={stats['referrals']}, Avg Wait={stats['avg_wait']}d")

        r = await client.get(f"{BASE_URL}/admin/analytics")
        assert r.status_code == 200
        analytics = r.json()
        print(f"   [+] Analytics loaded: {len(analytics['referral_volume'])} volume months, {len(analytics['specialty_distribution'])} specialties tracked")

    print("\n==================================================")
    print(" ALL 16 INTEGRATION WORKFLOW TESTS PASSED (100%)")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
