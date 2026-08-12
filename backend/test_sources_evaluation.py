import os
import json
import glob
import urllib.request
import urllib.parse
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/api/v1"
PDF_DIR = Path("d:/CTS Mock/test sources/synthetic_us_medical_documents_200")
IMAGE_DIR = Path("d:/CTS Mock/test sources/Dataset/images")
GROUND_TRUTH_FILE = PDF_DIR / "ground_truth.json"

def upload_file_to_api(file_path: Path):
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    boundary = "----CarePathTestBoundary" + os.urandom(8).hex()
    ext = file_path.suffix.lower()
    
    if ext == ".pdf":
        mime_type = "application/pdf"
    elif ext in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"
    elif ext == ".png":
        mime_type = "image/png"
    elif ext == ".webp":
        mime_type = "image/webp"
    else:
        mime_type = "application/octet-stream"

    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8")
    footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    payload = header + file_bytes + footer

    req = urllib.request.Request(
        f"{BASE_URL}/referrals/upload-document",
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def test_pdf_sources():
    print("\n" + "="*80)
    print(" 1. TESTING PDF TEST SOURCES (synthetic_us_medical_documents_200)")
    print("="*80)
    
    with open(GROUND_TRUTH_FILE, "r") as f:
        gt_list = json.load(f)
    gt_map = {item["file"]: item for item in gt_list}

    # Select representative sample across diverse diagnoses
    sample_files = [
        "medical_document_0001.pdf", # Diabetes
        "medical_document_0002.pdf", # Hyperlipidemia
        "medical_document_0003.pdf", # Iron Deficiency Anemia
        "medical_document_0004.pdf", # Acute Bronchitis
        "medical_document_0007.pdf", # UTI
        "medical_document_0017.pdf", # Hypothyroidism
        "medical_document_0018.pdf", # GERD
        "medical_document_0033.pdf", # Essential Hypertension
    ]

    pdf_results = []
    for fname in sample_files:
        fpath = PDF_DIR / fname
        if not fpath.exists():
            continue
        gt = gt_map.get(fname, {})
        print(f"\n[Testing PDF] {fname}")
        print(f" -> Ground Truth Diagnosis: {gt.get('diagnosis')}")
        print(f" -> Ground Truth Rx: {gt.get('prescription', {}).get('medication')}")
        
        res = upload_file_to_api(fpath)
        print(f" -> AI Detected Specialty : {res.get('detected_specialty')}")
        print(f" -> AI Detected Urgency   : {res.get('detected_urgency')}")
        print(f" -> Extracted Symptoms    : {res.get('symptoms')}")
        print(f" -> Extracted Conditions  : {res.get('conditions')}")
        print(f" -> Groq LLM Extracted    : {res.get('groq_extracted')}")
        pdf_results.append((fname, gt.get('diagnosis'), res.get('detected_specialty'), res.get('groq_extracted')))

    return pdf_results

def test_image_sources():
    print("\n" + "="*80)
    print(" 2. TESTING IMAGE TEST SOURCES (Dataset/images OCR & Clinical Ingestion)")
    print("="*80)
    
    sample_images = [
        "1.jpeg",
        "7.jpg",
        "12.jpeg",
        "25.jpeg",
        "134.png",
        "153.png",
    ]

    image_results = []
    for fname in sample_images:
        fpath = IMAGE_DIR / fname
        if not fpath.exists():
            continue
        print(f"\n[Testing Image] {fname} ({fpath.stat().st_size} bytes)")
        res = upload_file_to_api(fpath)
        print(f" -> AI Detected Specialty : {res.get('detected_specialty')}")
        print(f" -> AI Detected Urgency   : {res.get('detected_urgency')}")
        print(f" -> Extracted Symptoms    : {res.get('symptoms')}")
        print(f" -> Extracted Conditions  : {res.get('conditions')}")
        print(f" -> Insurance Network     : {res.get('insurance_network')}")
        image_results.append((fname, res.get('detected_specialty'), res.get('detected_urgency')))

    return image_results

if __name__ == "__main__":
    pdf_res = test_pdf_sources()
    img_res = test_image_sources()
    print("\n" + "="*80)
    print(" SUMMARY OF TEST SOURCE EVALUATION")
    print("="*80)
    print(f"PDFs Tested: {len(pdf_res)}")
    for f, diag, spec, groq in pdf_res:
        print(f"  - {f}: Diagnosis '{diag}' => Specialty '{spec}' (Groq: {groq})")
    print(f"\nImages Tested: {len(img_res)}")
    for f, spec, urg in img_res:
        print(f"  - {f}: Extracted Specialty '{spec}', Urgency '{urg}'")
    print("="*80)
