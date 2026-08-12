import pypdf
import os
import json
import dotenv
from groq import Groq

dotenv.load_dotenv('d:/CTS Mock/backend/.env')

pdf_path = 'd:/CTS Mock/test sources/synthetic_us_medical_documents_200/medical_document_0002.pdf'
reader = pypdf.PdfReader(pdf_path)
text = ''.join([p.extract_text() or '' for p in reader.pages])

client = Groq(api_key=os.getenv('GROQ_API_KEY'))
prompt = (
    "You are an expert clinical NLP system for medical referrals.\n"
    "Analyze the following clinical document and extract key information in strictly JSON format.\n\n"
    f"DOCUMENT CONTENT:\n{text[:4000]}\n\n"
    "Return a valid JSON object with the following fields:\n"
    "- target_specialty: (Single string. Must be a standard medical specialty matching diagnosis/labs e.g. INTERNAL MEDICINE, CARDIOVASCULAR DISEASE, ENDOCRINOLOGY, DIABETES & METABOLISM, GASTROENTEROLOGY, NEUROLOGY, DERMATOLOGY, PULMONARY DISEASE, ORTHOPEDIC SURGERY, UROLOGY, NEPHROLOGY, RHEUMATOLOGY, OPHTHALMOLOGY, PSYCHIATRY)\n"
    "- urgency: (Must be 'routine', 'urgent', or 'emergent')\n"
    "- symptoms: (Array of string symptoms or lab findings. If no physical symptoms are explicitly stated, include key abnormal lab results or clinical findings e.g. 'Elevated Total Cholesterol (228 mg/dL)', 'Elevated LDL (151 mg/dL)')\n"
    "- conditions: (Array of string medical conditions/diagnoses e.g. 'Hyperlipidemia')\n"
    "- insurance_network: (String insurance provider if mentioned, or default 'Aetna PPO')\n"
    "- max_distance_km: (Integer max distance in km, default 50)\n"
)

resp = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},
    temperature=0.1
)

print("=== ENHANCED GROQ OUTPUT ===")
print(resp.choices[0].message.content)
