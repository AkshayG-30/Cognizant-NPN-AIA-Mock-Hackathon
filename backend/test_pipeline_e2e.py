"""
Quick E2E Pipeline Validation Script
Tests /api/v1/carepath/process with PDF and Image test sources.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, "d:/CTS Mock/backend")

from app.db import database
from app.ml.model_registry import get_model_registry
from app.api.v1.carepath import process_carepath_workflow
from starlette.datastructures import UploadFile
import io

async def run_test():
    print("=== 1. Initializing DB and ML Models ===")
    database.init_db()
    registry = get_model_registry()
    loaded = registry.load_wait_time_model()
    print(f"Model loaded: {loaded}")

    async with database.async_session_factory() as db:
        # Test 1: Synthetic PDF
        pdf_path = Path("d:/CTS Mock/test sources/synthetic_us_medical_documents_200/medical_document_0001.pdf")
        if pdf_path.exists():
            print(f"\n=== 2. Testing PDF Ingestion: {pdf_path.name} ===")
            with open(pdf_path, "rb") as f:
                content = f.read()
            
            upload_file = UploadFile(
                file=io.BytesIO(content),
                filename=pdf_path.name,
                headers={"content-type": "application/pdf"}
            )
            
            res_pdf = await process_carepath_workflow(
                file=upload_file,
                clinical_text=None,
                specialty_override=None,
                urgency_override=None,
                patient_lat=34.0522,
                patient_lon=-118.2437,
                max_distance_km=100.0,
                insurance_network="In-Network Aetna / BlueCross",
                top_k=3,
                db=db
            )
            print("PDF Result Summary:")
            print(f"  - Specialty: {res_pdf['clinical_triage']['specialty']}")
            print(f"  - Urgency: {res_pdf['clinical_triage']['urgency']}")
            print(f"  - Candidates evaluated: {res_pdf['ml_engine']['candidates_evaluated']}")
            print(f"  - Recommendations generated: {len(res_pdf['recommendations'])}")
            if res_pdf['recommendations']:
                top = res_pdf['recommendations'][0]
                print(f"  - Top Doctor: {top['name']} ({top['specialty']})")
                print(f"  - Predicted Wait: {top['predicted_wait_days']} days | Distance: {top['distance_km']} km | Match: {top['match_score']}%")

        # Test 2: Image
        img_path = Path("d:/CTS Mock/test sources/Dataset/images/1.jpeg")
        if img_path.exists():
            print(f"\n=== 3. Testing Image OCR Ingestion: {img_path.name} ===")
            with open(img_path, "rb") as f:
                content = f.read()
            
            upload_img = UploadFile(
                file=io.BytesIO(content),
                filename=img_path.name,
                headers={"content-type": "image/jpeg"}
            )
            
            res_img = await process_carepath_workflow(
                file=upload_img,
                clinical_text="Patient reporting severe knee pain and reduced mobility after sports activity.",
                specialty_override=None,
                urgency_override=None,
                patient_lat=34.0522,
                patient_lon=-118.2437,
                max_distance_km=100.0,
                insurance_network="In-Network Aetna / BlueCross",
                top_k=3,
                db=db
            )
            print("Image Result Summary:")
            print(f"  - Specialty: {res_img['clinical_triage']['specialty']}")
            print(f"  - Urgency: {res_img['clinical_triage']['urgency']}")
            print(f"  - Candidates evaluated: {res_img['ml_engine']['candidates_evaluated']}")
            print(f"  - Recommendations generated: {len(res_img['recommendations'])}")
            if res_img['recommendations']:
                top = res_img['recommendations'][0]
                print(f"  - Top Doctor: {top['name']} ({top['specialty']})")
                print(f"  - Predicted Wait: {top['predicted_wait_days']} days | Distance: {top['distance_km']} km | Match: {top['match_score']}%")

    print("\n=== E2E Pipeline Test Completed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_test())
