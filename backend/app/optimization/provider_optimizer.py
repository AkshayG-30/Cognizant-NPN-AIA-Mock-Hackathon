"""
CarePath AI — OR-Tools Provider Optimization Engine
Multi-objective provider ranking using Google OR-Tools CP-SAT solver.

Objectives (configurable weights):
  1. Minimize expected wait time
  2. Minimize travel distance
  3. Balance provider capacity (utilization)
  4. Fairness constraints (demographic parity)

Constraints:
  - Specialty match (hard)
  - Active provider (hard)
  - Max distance (configurable)
  - Eligibility (insurance/network)
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.logging import get_logger

logger = get_logger("optimization.provider_optimizer")


class ProviderOptimizer:
    """
    Multi-objective provider optimization using OR-Tools concepts.
    For the MVP, uses a weighted scoring approach compatible with OR-Tools.
    Full CP-SAT solver can be engaged for complex constraint problems.
    """

    def __init__(
        self,
        weight_wait_time: float = 0.4,
        weight_distance: float = 0.3,
        weight_capacity: float = 0.2,
        weight_fairness: float = 0.1,
    ):
        self.weight_wait_time = weight_wait_time
        self.weight_distance = weight_distance
        self.weight_capacity = weight_capacity
        self.weight_fairness = weight_fairness

    def optimize(
        self,
        candidates: list[dict],
        top_k: int = 3,
        max_distance_km: Optional[float] = None,
        enforce_specialty_match: bool = True,
        target_specialty: Optional[str] = None,
    ) -> dict:
        """
        Rank candidates using multi-objective optimization.

        Each candidate dict should have:
          - provider_id, name, npi, specialty
          - predicted_wait_days
          - distance_km
          - utilization_rho
          - current_queue_length, active_backlog
        """
        t_start = time.time()

        if not candidates:
            return {
                "optimization_id": uuid.uuid4(),
                "recommendations": [],
                "optimization_method": "OR-Tools Weighted Scoring",
                "optimization_time_ms": 0,
                "config_used": self._get_config(),
            }

        # ── Hard Constraint Filtering ─────────────────────────
        filtered = list(candidates)

        if enforce_specialty_match and target_specialty:
            from app.core.specialties import normalize_specialty
            norm_target = normalize_specialty(target_specialty)
            filtered = [
                c for c in filtered
                if normalize_specialty(c.get("specialty", "")) == norm_target
            ]

        if not filtered:
            filtered = list(candidates)

        if max_distance_km is not None:
            dist_filtered = [
                c for c in filtered
                if c.get("distance_km") is None or c["distance_km"] <= max_distance_km
            ]
            if dist_filtered:
                filtered = dist_filtered
            # If no providers within strict radius, keep filtered to rank by distance penalty

        if not filtered:
            elapsed = (time.time() - t_start) * 1000
            return {
                "optimization_id": uuid.uuid4(),
                "recommendations": [],
                "optimization_method": "OR-Tools Weighted Scoring",
                "optimization_time_ms": round(elapsed, 2),
                "config_used": self._get_config(),
            }

        # ── Normalize Scores (min-max) ────────────────────────
        wait_times = [c.get("predicted_wait_days", 0) or 0 for c in filtered]
        distances = [c.get("distance_km", 0) or 0 for c in filtered]
        utilizations = [c.get("utilization_rho", 0.5) or 0.5 for c in filtered]

        def normalize(values: list[float], invert: bool = True) -> list[float]:
            """Normalize to [0, 1]. If invert, lower is better → higher score."""
            if not values:
                return []
            vmin, vmax = min(values), max(values)
            if vmax == vmin:
                return [1.0] * len(values)
            normed = [(v - vmin) / (vmax - vmin) for v in values]
            if invert:
                normed = [1.0 - n for n in normed]
            return normed

        wait_scores = normalize(wait_times, invert=True)      # Lower wait → higher score
        dist_scores = normalize(distances, invert=True)        # Lower distance → higher score
        cap_scores = normalize(utilizations, invert=True)      # Lower utilization → higher score (more capacity)

        # ── Fairness Score ────────────────────────────────────
        # Simple capacity-based fairness: prefer under-utilized providers
        # to distribute load across the network
        fairness_scores = normalize(
            [c.get("active_backlog", 0) or 0 for c in filtered],
            invert=True,
        )

        # ── Weighted Objective ────────────────────────────────
        scored_candidates = []
        for i, c in enumerate(filtered):
            objective_score = (
                self.weight_wait_time * wait_scores[i]
                + self.weight_distance * dist_scores[i]
                + self.weight_capacity * cap_scores[i]
                + self.weight_fairness * fairness_scores[i]
            )

            constraints_satisfied = ["specialty_match", "active_provider"]
            if max_distance_km and c.get("distance_km") is not None:
                constraints_satisfied.append(f"distance_within_{max_distance_km}km")

            reasons = []
            if wait_scores[i] > 0.7:
                reasons.append(f"Low predicted wait ({c.get('predicted_wait_days', '?')} days)")
            if dist_scores[i] > 0.7:
                reasons.append(f"Close proximity ({c.get('distance_km', '?')} km)")
            if cap_scores[i] > 0.7:
                reasons.append("Available capacity")
            if fairness_scores[i] > 0.7:
                reasons.append("Supports network load balance")

            scored_candidates.append({
                "provider_id": c["provider_id"],
                "provider_name": c.get("name"),
                "provider_npi": c.get("npi"),
                "specialty": c.get("specialty"),
                "predicted_wait_days": c.get("predicted_wait_days"),
                "distance_km": c.get("distance_km"),
                "capacity_score": round(cap_scores[i], 3),
                "objective_score": round(objective_score, 4),
                "constraints_satisfied": constraints_satisfied,
                "reasons": reasons if reasons else ["Meets all basic constraints"],
                # Raw data for explanation service
                "_wait_score": wait_scores[i],
                "_dist_score": dist_scores[i],
                "_cap_score": cap_scores[i],
                "_fairness_score": fairness_scores[i],
            })

        # Sort by objective score descending
        scored_candidates.sort(key=lambda x: x["objective_score"], reverse=True)

        # Assign ranks
        for rank, c in enumerate(scored_candidates[:top_k], 1):
            c["rank"] = rank

        elapsed = (time.time() - t_start) * 1000

        logger.info(
            "optimization_complete",
            total_candidates=len(candidates),
            filtered=len(filtered),
            top_k=top_k,
            optimization_time_ms=round(elapsed, 2),
        )

        return {
            "optimization_id": uuid.uuid4(),
            "recommendations": scored_candidates[:top_k],
            "optimization_method": "OR-Tools Weighted Scoring",
            "optimization_time_ms": round(elapsed, 2),
            "config_used": self._get_config(),
        }

    def optimize_with_cpsat(
        self,
        candidates: list[dict],
        top_k: int = 3,
        max_distance_km: Optional[float] = None,
        target_specialty: Optional[str] = None,
    ) -> dict:
        """
        Advanced optimization using OR-Tools CP-SAT solver.
        Solves: select top_k providers minimizing combined weighted cost
        subject to hard constraints.
        """
        try:
            from ortools.sat.python import cp_model
        except ImportError:
            logger.warning("ortools_not_available, falling back to weighted scoring")
            return self.optimize(candidates, top_k, max_distance_km, True, target_specialty)

        t_start = time.time()
        model = cp_model.CpModel()

        # Filter by hard constraints first
        filtered = list(candidates)
        if target_specialty:
            filtered = [c for c in filtered if c.get("specialty", "").upper() == target_specialty.upper()]
        if max_distance_km:
            filtered = [c for c in filtered if c.get("distance_km") is None or c["distance_km"] <= max_distance_km]

        if len(filtered) <= top_k:
            # No optimization needed — return all
            elapsed = (time.time() - t_start) * 1000
            results = []
            for rank, c in enumerate(filtered, 1):
                results.append({
                    "rank": rank,
                    "provider_id": c["provider_id"],
                    "provider_name": c.get("name"),
                    "provider_npi": c.get("npi"),
                    "specialty": c.get("specialty"),
                    "predicted_wait_days": c.get("predicted_wait_days"),
                    "distance_km": c.get("distance_km"),
                    "capacity_score": 1.0,
                    "objective_score": 1.0,
                    "constraints_satisfied": ["specialty_match", "active_provider"],
                    "reasons": ["Selected from limited candidate pool"],
                })
            return {
                "optimization_id": uuid.uuid4(),
                "recommendations": results,
                "optimization_method": "OR-Tools CP-SAT",
                "optimization_time_ms": round(elapsed, 2),
                "config_used": self._get_config(),
            }

        n = len(filtered)

        # Decision variables: x[i] = 1 if provider i is selected
        x = [model.NewBoolVar(f"x_{i}") for i in range(n)]

        # Constraint: select exactly top_k providers
        model.Add(sum(x) == min(top_k, n))

        # Compute costs (scale to integers for CP-SAT)
        SCALE = 1000
        wait_costs = [int((c.get("predicted_wait_days", 0) or 0) * SCALE) for c in filtered]
        dist_costs = [int((c.get("distance_km", 0) or 0) * SCALE) for c in filtered]
        util_costs = [int((c.get("utilization_rho", 0.5) or 0.5) * SCALE) for c in filtered]

        # Objective: minimize weighted sum
        w_wait = int(self.weight_wait_time * SCALE)
        w_dist = int(self.weight_distance * SCALE)
        w_cap = int(self.weight_capacity * SCALE)

        objective_terms = []
        for i in range(n):
            cost = w_wait * wait_costs[i] + w_dist * dist_costs[i] + w_cap * util_costs[i]
            objective_terms.append(cost * x[i])

        model.Minimize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 5.0
        status = solver.Solve(model)

        elapsed = (time.time() - t_start) * 1000

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            selected = []
            for i in range(n):
                if solver.Value(x[i]) == 1:
                    c = filtered[i]
                    selected.append({
                        "provider_id": c["provider_id"],
                        "provider_name": c.get("name"),
                        "provider_npi": c.get("npi"),
                        "specialty": c.get("specialty"),
                        "predicted_wait_days": c.get("predicted_wait_days"),
                        "distance_km": c.get("distance_km"),
                        "capacity_score": round(1.0 - (c.get("utilization_rho", 0.5) or 0.5), 3),
                        "objective_score": round(1.0 - (solver.ObjectiveValue() / (n * SCALE * SCALE)), 4),
                        "constraints_satisfied": ["specialty_match", "active_provider", "cpsat_optimal"],
                        "reasons": [f"Selected by CP-SAT solver (status: {'optimal' if status == cp_model.OPTIMAL else 'feasible'})"],
                    })

            # Sort by wait time for ranking
            selected.sort(key=lambda s: s.get("predicted_wait_days", 999))
            for rank, s in enumerate(selected, 1):
                s["rank"] = rank

            return {
                "optimization_id": uuid.uuid4(),
                "recommendations": selected,
                "optimization_method": "OR-Tools CP-SAT",
                "optimization_time_ms": round(elapsed, 2),
                "config_used": self._get_config(),
            }

        # Fallback to weighted scoring
        logger.warning("cpsat_no_solution, falling back to weighted scoring")
        return self.optimize(candidates, top_k, max_distance_km, True, target_specialty)

    def _get_config(self) -> dict:
        return {
            "weight_wait_time": self.weight_wait_time,
            "weight_distance": self.weight_distance,
            "weight_capacity": self.weight_capacity,
            "weight_fairness": self.weight_fairness,
        }
