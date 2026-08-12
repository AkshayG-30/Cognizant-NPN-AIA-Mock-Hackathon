import urllib.request
import json

pdf_path = 'd:/CTS Mock/test sources/synthetic_us_medical_documents_200/medical_document_0002.pdf'
with open(pdf_path, 'rb') as f:
    pdf_bytes = f.read()

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
header = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="medical_document_0002.pdf"\r\nContent-Type: application/pdf\r\n\r\n'.encode()
footer = f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/referrals/upload-document',
    data=header + pdf_bytes + footer,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print('=== UPLOAD TEST RESULT FOR DOCUMENT 0002 ===')
    print('Groq Extracted:', res.get('groq_extracted'))
    print('Specialty:', res.get('detected_specialty'))
    print('Urgency:', res.get('detected_urgency'))
    print('Symptoms:', res.get('symptoms'))
    print('Conditions:', res.get('conditions'))
    print('Insurance:', res.get('insurance_network'))
    print('Distance:', res.get('max_distance_km'))
