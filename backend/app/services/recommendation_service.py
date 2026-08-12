"""
CarePath AI — Recommendation Service
Orchestrates the complete recommendation pipeline:
  Referral → Analysis → Candidates → Prediction → Optimization → Explanation
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.models import (
    Recommendation,
    RecommendationCandidate,
    ReferralEvent,
    ReferralStatus,
    EventType,
)
from app.optimization.provider_optimizer import ProviderOptimizer
from app.services.provider_service import ProviderService
from app.services.referral_service import ReferralService
from app.services.wait_prediction_service import WaitPredictionService

logger = get_logger("services.recommendation")


class RecommendationService:
    """Orchestrates the end-to-end recommendation pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.referral_service = ReferralService(db)
        self.provider_service = ProviderService(db)
        self.wait_service = WaitPredictionService(db)

    async def generate(
        self,
        referral_id: uuid.UUID,
        top_k: int = 3,
        max_distance_km: float = 50.0,
        weight_wait_time: float = 0.4,
        weight_distance: float = 0.3,
        weight_capacity: float = 0.2,
        weight_fairness: float = 0.1,
    ) -> dict:
        """Generate provider recommendations for a referral."""
        t_start = time.time()

        # 1. Retrieve referral
        referral = await self.referral_service.get_by_id(referral_id)

        # 2. Analyze if not already analyzed
        if referral.status in (ReferralStatus.DRAFT, ReferralStatus.SUBMITTED):
            await self.referral_service.analyze(referral_id)
            await self.db.flush()
            referral = await self.referral_service.get_by_id(referral_id)

        # 3. Identify specialty
        specialty = referral.inferred_specialty or referral.target_specialty
        if not specialty:
            raise ValidationError(
                "Cannot generate recommendations without a target specialty.",
                details={"referral_id": str(referral_id)},
            )

        # 4. Generate provider candidates
        candidates = await self.provider_service.get_candidates_for_optimization(
            specialty=specialty,
            state=None,  # Could use patient's state
            latitude=referral.preferred_location_lat,
            longitude=referral.preferred_location_lng,
            max_distance_km=max_distance_km or referral.max_distance_km or 50.0,
            limit=100,
        )

        if not candidates:
            logger.warning("no_candidates_found", specialty=specialty, referral_id=str(referral_id))
            # Still return a valid response with empty recommendations
            recommendation = Recommendation(
                id=uuid.uuid4(),
                referral_id=referral_id,
                optimization_method="OR-Tools Weighted Scoring",
                optimization_config={
                    "weight_wait_time": weight_wait_time,
                    "weight_distance": weight_distance,
                    "weight_capacity": weight_capacity,
                    "weight_fairness": weight_fairness,
                },
                optimization_time_ms=0,
                top_k=top_k,
                explanation_text="No eligible providers found matching the referral criteria.",
            )
            self.db.add(recommendation)
            elapsed = (time.time() - t_start) * 1000
            return {
                "recommendation_id": recommendation.id,
                "referral_id": referral_id,
                "recommendations": [],
                "optimization_method": "OR-Tools Weighted Scoring",
                "explanation": "No eligible providers found matching the referral criteria.",
                "optimization_time_ms": round(elapsed, 2),
                "timestamp": datetime.now(timezone.utc),
            }

        # 5. Predict wait times for all candidates
        for candidate in candidates:
            try:
                wait_days = await self.wait_service.predict_for_candidate(candidate)
                candidate["predicted_wait_days"] = wait_days
            except Exception as e:
                logger.warning("prediction_failed_for_candidate", error=str(e))
                candidate["predicted_wait_days"] = None

        # 6. Run optimization
        optimizer = ProviderOptimizer(
            weight_wait_time=weight_wait_time,
            weight_distance=weight_distance,
            weight_capacity=weight_capacity,
            weight_fairness=weight_fairness,
        )

        opt_result = optimizer.optimize(
            candidates=candidates,
            top_k=top_k,
            max_distance_km=max_distance_km,
            target_specialty=specialty,
        )

        # 7. Store recommendation snapshot
        recommendation = Recommendation(
            id=opt_result["optimization_id"],
            referral_id=referral_id,
            optimization_method=opt_result["optimization_method"],
            optimization_config=opt_result["config_used"],
            optimization_time_ms=opt_result["optimization_time_ms"],
            top_k=top_k,
        )
        self.db.add(recommendation)

        # Store individual candidates
        for rec in opt_result["recommendations"]:
            candidate_record = RecommendationCandidate(
                recommendation_id=recommendation.id,
                provider_id=rec["provider_id"],
                rank=rec["rank"],
                predicted_wait_days=rec.get("predicted_wait_days"),
                distance_km=rec.get("distance_km"),
                capacity_score=rec.get("capacity_score"),
                objective_score=rec["objective_score"],
                constraints_satisfied=rec.get("constraints_satisfied", []),
                reasons=rec.get("reasons", []),
            )
            self.db.add(candidate_record)

        # 8. Generate explanation
        explanation = self._generate_explanation(opt_result["recommendations"], specialty)
        recommendation.explanation_text = explanation

        # Audit event
        event = ReferralEvent(
            referral_id=referral_id,
            event_type=EventType.RECOMMENDATION_GENERATED,
            event_data={
                "recommendation_id": str(recommendation.id),
                "candidates_evaluated": len(candidates),
                "recommendations_generated": len(opt_result["recommendations"]),
            },
        )
        self.db.add(event)

        # Update referral status
        referral.status = ReferralStatus.PENDING_REVIEW
        referral.updated_at = datetime.now(timezone.utc)

        elapsed = (time.time() - t_start) * 1000

        logger.info(
            "recommendation_generated",
            referral_id=str(referral_id),
            recommendation_id=str(recommendation.id),
            candidates=len(candidates),
            recommendations=len(opt_result["recommendations"]),
            total_time_ms=round(elapsed, 2),
        )

        return {
            "recommendation_id": recommendation.id,
            "referral_id": referral_id,
            "recommendations": opt_result["recommendations"],
            "optimization_method": opt_result["optimization_method"],
            "explanation": explanation,
            "optimization_time_ms": opt_result["optimization_time_ms"],
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_explanation(self, recommendation_id: uuid.UUID) -> dict:
        """Get or regenerate explanation for a recommendation."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )
        recommendation = result.scalar_one_or_none()
        if not recommendation:
            raise NotFoundError("Recommendation", str(recommendation_id))

        # Load candidates
        cand_result = await self.db.execute(
            select(RecommendationCandidate)
            .where(RecommendationCandidate.recommendation_id == recommendation_id)
            .order_by(RecommendationCandidate.rank)
        )
        candidates = list(cand_result.scalars().all())

        if recommendation.explanation_text:
            explanation = recommendation.explanation_text
        else:
            # Regenerate from candidate data
            recs = []
            for c in candidates:
                recs.append({
                    "rank": c.rank,
                    "predicted_wait_days": c.predicted_wait_days,
                    "distance_km": c.distance_km,
                    "constraints_satisfied": c.constraints_satisfied,
                    "reasons": c.reasons,
                })
            explanation = self._generate_explanation(recs, "Unknown")

        return {
            "recommendation_id": recommendation_id,
            "explanation": explanation,
            "evidence": {
                "candidates_count": len(candidates),
                "optimization_method": recommendation.optimization_method,
                "config": recommendation.optimization_config,
            },
            "generated_at": datetime.now(timezone.utc),
        }

    def _generate_explanation(self, recommendations: list[dict], specialty: str) -> str:
        """
        Generate evidence-grounded explanation from actual optimization outputs.
        NO LLM invention — only actual system data is used.
        """
        if not recommendations:
            return f"No providers found matching the requested specialty '{specialty}'."

        lines = [f"CarePath AI evaluated providers for {specialty} and ranked them based on predicted wait time, distance, capacity availability, and network load balance.\n"]

        for rec in recommendations:
            rank = rec.get("rank", "?")
            name = rec.get("provider_name", "Provider")
            wait = rec.get("predicted_wait_days")
            dist = rec.get("distance_km")
            reasons = rec.get("reasons", [])

            parts = [f"Rank #{rank}: {name}"]
            if wait is not None:
                parts.append(f"predicted wait of {wait} days")
            if dist is not None:
                parts.append(f"{dist} km from the preferred location")

            constraints = rec.get("constraints_satisfied", [])
            if constraints:
                parts.append(f"satisfying constraints: {', '.join(constraints)}")

            line = " — ".join(parts) + "."
            if reasons:
                line += f" Key factors: {'; '.join(reasons)}."

            lines.append(line)

        lines.append("\nNote: This is a clinical decision-support recommendation. Final routing decisions must be reviewed by a clinician or care coordinator.")

        return "\n".join(lines)
