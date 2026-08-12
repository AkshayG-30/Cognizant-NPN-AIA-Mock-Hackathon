import os
import json
import dotenv
import sys
import io
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
dotenv.load_dotenv('d:/CTS Mock/backend/.env')
from groq import Groq

client = Groq(api_key=os.getenv('GROQ_API_KEY'))
ocr_engine = RapidOCR()

IMAGE_DIR = "d:/CTS Mock/test sources/Dataset/images"

image_samples = [
    "7.jpg",
    "12.jpeg",
    "134.png",
    "153.png",
    "180.jpeg",
    "190.jpeg",
]

print("=== EVALUATING TARGET SPECIALTY ON IMAGES (OCR + GROQ NLP) ===")
for img_name in image_samples:
    img_path = os.path.join(IMAGE_DIR, img_name)
    if not os.path.exists(img_path):
        continue
    img = Image.open(img_path).convert("RGB")
    ocr_result, _ = ocr_engine(np.array(img))
    lines = [r[1] for r in (ocr_result or [])]
    ocr_text = "\n".join(lines)
    
    prompt = (
        "You are an expert clinical NLP triage system for medical prescriptions and scans.\n"
        "Analyze the following OCR text extracted from a patient prescription or medical scan.\n"
        "Identify the primary health issue, medication purpose, and best specialist recommendation.\n"
        "Categories to choose from:\n"
        "- CARDIOVASCULAR DISEASE (e.g. cholesterol, statins, blood pressure, heart)\n"
        "- ORTHOPEDIC SURGERY (e.g. knee pain, joints, bones, anti-inflammatory, calcium)\n"
        "- DERMATOLOGY (e.g. skin, fungal infections, itraconazole, medicated shampoo)\n"
        "- PULMONARY DISEASE (e.g. asthma, bronchitis, respiratory, inhalers)\n"
        "- GASTROENTEROLOGY (e.g. gastritis, omeprazole, reflux, peptic)\n"
        "- INTERNAL MEDICINE (e.g. fever, headache, pain, general infections, antibiotics)\n\n"
        f"OCR EXTRACTED TEXT:\n{ocr_text[:3000]}\n\n"
        "Return JSON with keys: target_specialty, urgency, symptoms, conditions, detected_medications."
    )
    
    resp = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[{'role': 'user', 'content': prompt}],
        response_format={'type': 'json_object'},
        temperature=0.1,
    )
    data = json.loads(resp.choices[0].message.content)
    print(f"Image {img_name}:")
    print(f"  -> OCR Lines Found     : {len(lines)}")
    print(f"  -> Recommended Referral: {data.get('target_specialty')}")
    print(f"  -> Detected Symptoms   : {data.get('symptoms')}")
    print(f"  -> Detected Conditions : {data.get('conditions')}")
    print(f"  -> Detected Medications: {data.get('detected_medications')}\n")
