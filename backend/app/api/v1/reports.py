"""
CarePath AI — Medical Reports API
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/reports", tags=["Reports"])

# In-memory session store for uploaded patient reports (compatible with persistent referral linkage)
REPORTS_DB: list[dict] = [
    {
        "id": "rep_01",
        "name": "Comprehensive Metabolic & Lipid Panel",
        "kind": "Blood Test",
        "notes": "Total Cholesterol 228 mg/dL, LDL 151 mg/dL, Triglycerides 190 mg/dL",
        "file_name": "lipid_panel_2026.pdf",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
]


class ReportCreateRequest(BaseModel):
    name: str
    kind: str = "Blood Test"
    notes: Optional[str] = ""
    file_name: Optional[str] = ""


@router.get("/mine")
async def get_my_reports():
    return REPORTS_DB


@router.post("", status_code=201)
async def create_report(req: ReportCreateRequest):
    new_rep = {
        "id": f"rep_{uuid.uuid4().hex[:8]}",
        "name": req.name,
        "kind": req.kind,
        "notes": req.notes or "",
        "file_name": req.file_name or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    REPORTS_DB.insert(0, new_rep)
    return new_rep


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    global REPORTS_DB
    REPORTS_DB = [r for r in REPORTS_DB if r["id"] != report_id]
    return {"success": True, "deleted_id": report_id}
