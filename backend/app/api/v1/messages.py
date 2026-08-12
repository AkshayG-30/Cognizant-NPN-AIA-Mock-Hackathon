"""
CarePath AI — Messages API
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/messages", tags=["Messages"])

MESSAGES_DB: list[dict] = [
    {
        "id": "msg_01",
        "from_user_id": "doc_01",
        "from_name": "Dr. Sarah Williams, MD",
        "to_user_id": "patient_01",
        "body": "Hello! I reviewed your lipid panel results. We will discuss lifestyle optimizations and medical management during your upcoming consultation.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
]


class MessageSendRequest(BaseModel):
    to_user_id: str
    body: str


@router.get("")
async def get_messages():
    return MESSAGES_DB


@router.post("")
async def send_message(req: MessageSendRequest):
    new_msg = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "from_user_id": "patient_01",
        "from_name": "Jane Doe",
        "to_user_id": req.to_user_id,
        "body": req.body,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    MESSAGES_DB.insert(0, new_msg)
    return new_msg
