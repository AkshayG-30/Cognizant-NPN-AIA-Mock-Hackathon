import urllib.request
import json

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
with open('d:/CTS Mock/test sources/synthetic_us_medical_documents_200/medical_document_0001.pdf', 'rb') as f:
    content = f.read()

header = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="medical_document_0001.pdf"\r\nContent-Type: application/pdf\r\n\r\n'.encode()
footer = f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/referrals/upload-document',
    data=header + content + footer,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)

with urllib.request.urlopen(req) as resp:
    res_json = json.loads(resp.read().decode('utf-8'))
    print('Groq LLM Extracted:', res_json.get('groq_extracted'))
    print('Detected Specialty:', res_json.get('detected_specialty'))
    print('Detected Urgency:', res_json.get('detected_urgency'))
    print('Symptoms:', res_json.get('symptoms'))
    print('Conditions:', res_json.get('conditions'))
    print('Insurance Network:', res_json.get('insurance_network'))
