"""Test with specialty_override to check candidate counts."""
import urllib.request, json, urllib.parse

body = urllib.parse.urlencode({
    "clinical_text": "Patient with exertional chest pressure. LDL 165.",
    "patient_lat": 34.0522,
    "patient_lon": -118.2437,
    "specialty_override": "CARDIOVASCULAR DISEASE",
    "top_k": 5,
})
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/carepath/process",
    data=body.encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
res = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
ml = res.get("ml_engine", {})
print(f"Candidates evaluated: {ml.get('candidates_evaluated')}")
print(f"Avg predicted wait: {ml.get('average_predicted_wait_days')}")
recs = res.get("recommendations", [])
for r in recs[:5]:
    print(
        f"  #{r['rank']} {r['name']}: "
        f"quality={r['quality_score']}, "
        f"dist={r['distance_km']}km, "
        f"wait={r['predicted_wait_days']}d"
    )
