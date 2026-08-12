import os
import json
import dotenv
import pypdf
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
dotenv.load_dotenv('d:/CTS Mock/backend/.env')
from groq import Groq
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

test_cases = [
    ('0001', 'Type 2 Diabetes Mellitus'),
    ('0002', 'Hyperlipidemia'),
    ('0004', 'Acute bronchitis'),
    ('0007', 'Urinary tract infection'),
    ('0018', 'Gastroesophageal reflux disease'),
    ('0033', 'Essential Hypertension'),
]

print("=== EVALUATING TARGET SPECIALTY ON PDFS ===")
for doc_num, name in test_cases:
    fpath = f'd:/CTS Mock/test sources/synthetic_us_medical_documents_200/medical_document_{doc_num}.pdf'
    reader = pypdf.PdfReader(fpath)
    text = ''.join([p.extract_text() for p in reader.pages])
    prompt = (
        "You are an expert clinical triage and specialty routing AI.\n"
        "Given the patient's medical document, determine the best specialty for specialist referral.\n"
        "Do NOT simply return the originating primary care / internal medicine clinic header.\n"
        "Select the most appropriate specialist category from:\n"
        "- CARDIOVASCULAR DISEASE (for hyperlipidemia, high cholesterol, hypertension, cardiac issues)\n"
        "- PULMONARY DISEASE (for acute bronchitis, respiratory infections, asthma, cough)\n"
        "- UROLOGY or NEPHROLOGY (for urinary tract infections, renal conditions)\n"
        "- GASTROENTEROLOGY (for GERD, acid reflux, gastrointestinal disorders)\n"
        "- INTERNAL MEDICINE (for diabetes, metabolic monitoring, thyroid, or non-specific conditions)\n"
        "- ORTHOPEDIC SURGERY (for musculoskeletal, fractures, joint pain)\n"
        "- DERMATOLOGY (for skin rashes, lesions)\n\n"
        f"DOCUMENT:\n{text[:3000]}\n\n"
        "Return JSON with keys: target_specialty, urgency, symptoms, conditions."
    )
    resp = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[{'role': 'user', 'content': prompt}],
        response_format={'type': 'json_object'},
        temperature=0.1,
    )
    data = json.loads(resp.choices[0].message.content)
    print(f"Doc {doc_num} ({name}):")
    print(f"  -> Recommended Referral: {data.get('target_specialty')}")
    print(f"  -> Extracted Conditions: {data.get('conditions')}")
    print(f"  -> Key Findings        : {data.get('symptoms')}\n")
