"""
CarePath AI — FHIR R4 Mapper
Maps internal domain models to FHIR R4-compatible representations.
This is a prototype representation — NOT a certified FHIR implementation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.logging import get_logger
from app.db.models import Referral, Provider, Patient, UrgencyLevel

logger = get_logger("fhir.mapper")

# FHIR priority mapping
URGENCY_TO_FHIR_PRIORITY = {
    UrgencyLevel.ROUTINE: "routine",
    UrgencyLevel.URGENT: "urgent",
    UrgencyLevel.EMERGENT: "asap",
    UrgencyLevel.STAT: "stat",
}


class FHIRMapper:
    """Maps CarePath internal models to FHIR R4-compatible JSON resources."""

    @staticmethod
    def referral_to_service_request(
        referral: Referral,
        patient: Optional[Patient] = None,
    ) -> dict:
        """
        Convert a Referral to a FHIR R4 ServiceRequest resource.
        FHIR R4-compatible prototype representation.
        """
        service_request = {
            "resourceType": "ServiceRequest",
            "id": str(referral.id),
            "meta": {
                "versionId": "1",
                "lastUpdated": referral.updated_at.isoformat() if referral.updated_at else datetime.now(timezone.utc).isoformat(),
                "profile": ["http://hl7.org/fhir/StructureDefinition/ServiceRequest"],
                "tag": [
                    {
                        "system": "http://carepath.ai/tags",
                        "code": "prototype",
                        "display": "FHIR R4-compatible prototype representation"
                    }
                ],
            },
            "status": _referral_status_to_fhir(referral.status.value if hasattr(referral.status, 'value') else referral.status),
            "intent": "order",
        }

        # Category
        if referral.target_specialty or referral.inferred_specialty:
            specialty = referral.inferred_specialty or referral.target_specialty
            service_request["category"] = [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "display": specialty,
                }],
                "text": specialty,
            }]

        # Priority
        urgency = referral.urgency if hasattr(referral.urgency, 'value') else referral.urgency
        if urgency:
            urgency_enum = UrgencyLevel(urgency) if isinstance(urgency, str) else urgency
            service_request["priority"] = URGENCY_TO_FHIR_PRIORITY.get(urgency_enum, "routine")

        # Subject (Patient)
        if patient:
            service_request["subject"] = {
                "reference": f"Patient/{patient.id}",
                "display": f"{patient.first_name} {patient.last_name}",
            }
        elif referral.patient_id:
            service_request["subject"] = {
                "reference": f"Patient/{referral.patient_id}",
            }

        # Requester (Referring Provider)
        if referral.referring_provider_npi:
            service_request["requester"] = {
                "reference": f"Practitioner/{referral.referring_provider_npi}",
                "identifier": {
                    "system": "http://hl7.org/fhir/sid/us-npi",
                    "value": referral.referring_provider_npi,
                },
            }

        # Reason codes (conditions/symptoms)
        reason_codes = []
        if referral.conditions:
            for condition in referral.conditions:
                reason_codes.append({
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "display": condition,
                    }],
                    "text": condition,
                })
        if reason_codes:
            service_request["reasonCode"] = reason_codes

        # Clinical text as note
        if referral.clinical_text:
            service_request["note"] = [{
                "text": referral.clinical_text,
                "time": referral.created_at.isoformat() if referral.created_at else None,
            }]

        # Extensions for CarePath-specific data
        extensions = []
        if referral.symptoms:
            extensions.append({
                "url": "http://carepath.ai/fhir/extensions/symptoms",
                "valueString": ", ".join(referral.symptoms),
            })
        if referral.max_distance_km:
            extensions.append({
                "url": "http://carepath.ai/fhir/extensions/maxDistanceKm",
                "valueDecimal": referral.max_distance_km,
            })
        if referral.insurance_network:
            extensions.append({
                "url": "http://carepath.ai/fhir/extensions/insuranceNetwork",
                "valueString": referral.insurance_network,
            })
        if extensions:
            service_request["extension"] = extensions

        service_request["_carepath_disclaimer"] = (
            "FHIR R4-compatible prototype representation. "
            "Not certified for clinical use. "
            "Generated by CarePath AI for research and demonstration purposes."
        )

        return service_request

    @staticmethod
    def provider_to_practitioner(provider: Provider) -> dict:
        """Convert Provider to FHIR R4 Practitioner resource."""
        return {
            "resourceType": "Practitioner",
            "id": str(provider.id),
            "identifier": [{
                "system": "http://hl7.org/fhir/sid/us-npi",
                "value": provider.npi,
            }],
            "active": provider.is_active,
            "name": [{
                "family": provider.last_name,
                "given": [provider.first_name],
                "prefix": [provider.credential] if provider.credential and provider.credential != "UNKNOWN" else [],
            }],
            "gender": _map_gender(provider.gender),
            "qualification": [{
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "display": provider.specialty,
                    }],
                    "text": provider.specialty,
                },
            }] if provider.specialty else [],
            "_carepath_disclaimer": "FHIR R4-compatible prototype representation.",
        }

    @staticmethod
    def patient_to_fhir(patient: Patient) -> dict:
        """Convert Patient to FHIR R4 Patient resource."""
        resource = {
            "resourceType": "Patient",
            "id": str(patient.id),
            "active": True,
            "name": [{
                "family": patient.last_name,
                "given": [patient.first_name],
            }],
        }
        if patient.external_id:
            resource["identifier"] = [{
                "system": "http://carepath.ai/fhir/abha",
                "value": patient.external_id,
            }]
        if patient.gender:
            resource["gender"] = _map_gender(patient.gender)
        if patient.date_of_birth:
            resource["birthDate"] = patient.date_of_birth.strftime("%Y-%m-%d")
        resource["_carepath_disclaimer"] = "FHIR R4-compatible prototype representation."
        return resource

    @staticmethod
    def validate_service_request(resource: dict) -> list[str]:
        """Basic validation of a FHIR ServiceRequest resource."""
        errors = []
        if resource.get("resourceType") != "ServiceRequest":
            errors.append("resourceType must be 'ServiceRequest'")
        if not resource.get("status"):
            errors.append("status is required")
        if not resource.get("intent"):
            errors.append("intent is required")
        if resource.get("status") not in (
            "draft", "active", "on-hold", "revoked",
            "completed", "entered-in-error", "unknown"
        ):
            errors.append(f"Invalid status: {resource.get('status')}")
        return errors


def _referral_status_to_fhir(status: str) -> str:
    """Map internal referral status to FHIR ServiceRequest status."""
    mapping = {
        "draft": "draft",
        "submitted": "active",
        "analyzing": "active",
        "analyzed": "active",
        "pending_review": "active",
        "approved": "active",
        "scheduled": "active",
        "completed": "completed",
        "cancelled": "revoked",
        "rerouting": "on-hold",
    }
    return mapping.get(status, "unknown")


def _map_gender(gender: str | None) -> str:
    """Map internal gender to FHIR gender."""
    if not gender:
        return "unknown"
    g = gender.strip().lower()
    if g in ("male", "m"):
        return "male"
    elif g in ("female", "f"):
        return "female"
    return "unknown"
