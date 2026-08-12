import urllib.request
import json
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

boundary = '----WebKitFormBoundaryCarePathTest'

def upload_file(path, fname, mime):
    with open(path, 'rb') as f:
        data = f.read()
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'
        f'Content-Type: {mime}\r\n\r\n'
    ).encode('utf-8') + data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/referrals/upload-document',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode('utf-8'))

print("1. Testing Image Upload (134.png):")
img_res = upload_file('d:/CTS Mock/test sources/Dataset/images/134.png', '134.png', 'image/png')
print("  -> Detected Specialty:", img_res.get('detected_specialty'))
print("  -> Urgency           :", img_res.get('detected_urgency'))
print("  -> Extracted Symptoms:", img_res.get('symptoms'))
print("  -> Groq Extracted    :", img_res.get('groq_extracted'))
print("  -> Text Preview      :", img_res.get('extracted_text')[:100].replace('\n', ' '))

print("\n2. Testing PDF Upload (medical_document_0002.pdf):")
pdf_res = upload_file('d:/CTS Mock/test sources/synthetic_us_medical_documents_200/medical_document_0002.pdf', 'medical_document_0002.pdf', 'application/pdf')
print("  -> Detected Specialty:", pdf_res.get('detected_specialty'))
print("  -> Urgency           :", pdf_res.get('detected_urgency'))
print("  -> Extracted Symptoms:", pdf_res.get('symptoms'))
print("  -> Groq Extracted    :", pdf_res.get('groq_extracted'))
print("  -> Extracted Conds   :", pdf_res.get('conditions'))
