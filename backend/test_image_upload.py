import io
import json
import urllib.request
from PIL import Image, ImageDraw

img = Image.new('RGB', (800, 400), color=(255, 255, 255))
d = ImageDraw.Draw(img)
text_content = (
    "PATIENT REFERRAL NOTE\n"
    "Patient Name: Sarah Jenkins\n"
    "Specialty Requested: CARDIOVASCULAR DISEASE\n"
    "Urgency: Urgent\n"
    "Symptoms: Dyspnea on exertion, lower extremity edema, orthopnea\n"
    "Primary Diagnosis: Congestive Heart Failure, Essential Hypertension\n"
    "Insurance: Blue Cross Blue Shield\n"
    "Max Preferred Distance: 35 km"
)
d.text((20, 20), text_content, fill=(0, 0, 0))

buf = io.BytesIO()
img.save(buf, format='PNG')
img_bytes = buf.getvalue()

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
header = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="clinical_scan_001.png"\r\nContent-Type: image/png\r\n\r\n'.encode()
footer = f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/referrals/upload-document',
    data=header + img_bytes + footer,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print('=== IMAGE UPLOAD TEST RESULT ===')
    print('Groq Extracted:', res.get('groq_extracted'))
    print('Specialty:', res.get('detected_specialty'))
    print('Urgency:', res.get('detected_urgency'))
    print('Symptoms:', res.get('symptoms'))
    print('Conditions:', res.get('conditions'))
    print('Insurance:', res.get('insurance_network'))
    print('Distance:', res.get('max_distance_km'))
