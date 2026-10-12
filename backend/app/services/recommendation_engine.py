"""
AI Recommendation Engine Service
--------------------------------
Orchestrates the end-to-end multi-stage recommendation pipeline:
  1. Geographic Candidate Retrieval (Central + Citizen's State only)
  2. Deterministic Eligibility Pre-Filter (Phase 3 Engine)
  3. Registration Activity & Deadline Pre-Filter (Phase 4 Engine)
  4. Multi-Factor Relevance Ranking (OpenAI Structured Ranking or Explainable Fallback)
  5. Response Assembly with isolated Match Score (0-100) and Verification Queue

ARCHITECTURAL PRINCIPLE:
Eligibility is determined exclusively by the Phase 3 Deterministic Eligibility Engine.
The AI recommendation engine operates strictly AFTER deterministic eligibility and
activity validation. The match score (0-100) indicates profile & need relevance,
never legal qualification.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.integrations.openai_service import OpenAIService
from app.integrations.supabase_client import get_supabase_client
from app.models.deadline import ActivityStatus, DeadlineClassification, SchemeActivityInfo
from app.models.eligibility import (
    CriterionResult,
    EligibilityExplanation,
    EligibilityStatus,
    UserProfileInput,
)
from app.models.recommendation import (
    AIRankingOutput,
    RecommendationItem,
    RecommendationResponse,
    VerificationRequiredItem,
)
from app.services.deadline_service import get_scheme_activity
from app.services.eligibility_engine import evaluate_eligibility
from app.services.eligibility_service import EligibilityService

logger = logging.getLogger(__name__)


class DeterministicFallbackRanker:
    """
    Explainable multi-factor deterministic relevance ranker.
    Executed when OpenAI is unavailable, unconfigured, or returns invalid output.
    Computes a relevance match score (0–100) and human-readable explanation.
    """

    @staticmethod
    def calculate_relevance(
        scheme: Dict[str, Any],
        profile: UserProfileInput,
        activity: SchemeActivityInfo,
        query: Optional[str] = None,
    ) -> Tuple[int, str]:
        """
        Calculate a multi-factor relevance match score (0-100) and explainable reason.
        Factors:
          - Base qualified scheme relevance: 35 points
          - Query keyword relevance: up to 25 points
          - Occupation / demographic match: up to 20 points
          - Geographic proximity: up to 10 points
          - Deadline urgency: up to 10 points
        """
        score = 35  # Baseline for any verified ELIGIBLE and OPEN scheme
        reasons: List[str] = ["Eligible and active public welfare program"]

        scheme_name = str(scheme.get("scheme_name") or "").lower()
        description = str(scheme.get("description") or "").lower()
        benefits = str(scheme.get("benefits") or "").lower()
        scheme_text = f"{scheme_name} {description} {benefits}"

        # 1. Query Keyword Relevance (up to 25 pts)
        if query and query.strip():
            cleaned_query = query.strip().lower()
            query_tokens = [w for w in re.split(r"\W+", cleaned_query) if len(w) > 2]
            matched_tokens = [t for t in query_tokens if t in scheme_text]

            if matched_tokens:
                boost = min(len(matched_tokens) * 8, 25)
                score += boost
                reasons.append(f"Matches your search interest in '{', '.join(matched_tokens[:3])}'")

        # 2. Occupation Alignment (up to 15 pts)
        if profile.occupation:
            occ = profile.occupation.strip().lower()
            occ_synonyms = [occ]
            if "farm" in occ or "agri" in occ or "kisan" in occ:
                occ_synonyms.extend(["farm", "agri", "crop", "kisan", "cultivat"])
            elif "student" in occ:
                occ_synonyms.extend(["student", "scholarship", "education", "study", "fellowship"])
            elif "artisan" in occ or "craft" in occ:
                occ_synonyms.extend(["artisan", "weaver", "craft", "vishwakarma"])

            if any(syn in scheme_text for syn in occ_synonyms):
                score += 15
                reasons.append(f"Highly relevant to your occupation ({profile.occupation})")

        # 3. Category / Gender / Disability Relevance (up to 10 pts)
        if profile.category and profile.category.lower() in scheme_text:
            score += 5
            reasons.append(f"Includes specific provisions for {profile.category} community")

        if profile.disability_status and ("disab" in scheme_text or "divyang" in scheme_text):
            score += 10
            reasons.append("Contains targeted provisions for persons with disabilities")

        # 4. Geographic Specificity (up to 10 pts)
        if scheme.get("government_level") == "STATE":
            score += 10
            reasons.append("State-specific program tailored for your resident state")
        else:
            score += 5
            reasons.append("Central government pan-India program")

        # 5. Application Deadline Urgency (up to 10 pts)
        if activity.deadline_status == DeadlineClassification.CLOSING_TODAY:
            score += 10
            reasons.append("Application deadline is today — immediate action required")
        elif activity.deadline_status == DeadlineClassification.URGENT:
            score += 8
            reasons.append(
                f"Application deadline is urgent ({activity.days_remaining} day(s) remaining)"
            )
        elif activity.deadline_status == DeadlineClassification.APPROACHING:
            score += 4
            reasons.append(
                f"Application deadline is approaching ({activity.days_remaining} days remaining)"
            )

        # Clamp score to [0, 100]
        final_score = max(0, min(score, 100))
        final_reason = ". ".join(reasons) + "."

        return final_score, final_reason


class RecommendationService:
    """Service handling scheme filtering, eligibility verification, and ranking."""

    def __init__(
        self,
        openai_service: Optional[OpenAIService] = None,
        eligibility_service: Optional[EligibilityService] = None,
        client: Optional[Any] = None,
    ):
        self.openai_service = openai_service or OpenAIService()
        self.eligibility_service = eligibility_service or EligibilityService(client=client)
        self.client = client or get_supabase_client()

    def get_candidate_schemes(
        self, profile: UserProfileInput
    ) -> List[Dict[str, Any]]:
        """
        Geographic Pre-Filter:
        Retrieves Central schemes + schemes belonging strictly to user's selected state.
        Schemes restricted to other states are excluded BEFORE eligibility and ranking.
        """
        # 1. Fetch Central schemes
        central_res = (
            self.client.table("schemes")
            .select("*")
            .eq("government_level", "CENTRAL")
            .execute()
        )
        central_schemes = central_res.data or []

        # 2. Fetch State schemes if user has a designated state
        state_schemes: List[Dict[str, Any]] = []
        if profile.state_id is not None:
            state_res = (
                self.client.table("schemes")
                .select("*")
                .eq("government_level", "STATE")
                .eq("state_id", profile.state_id)
                .execute()
            )
            state_schemes = state_res.data or []

        return central_schemes + state_schemes

    def get_eligibility_rules_map(self, scheme_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Batch-query eligibility rules for given scheme IDs."""
        if not scheme_ids:
            return {}
        res = (
            self.client.table("scheme_eligibility")
            .select("*")
            .in_("scheme_id", scheme_ids)
            .execute()
        )
        rules_map: Dict[str, Dict[str, Any]] = {}
        for r in res.data or []:
            rules_map[r["scheme_id"]] = r
        return rules_map

    def recommend_schemes(
        self,
        profile: Optional[UserProfileInput] = None,
        user_id: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> RecommendationResponse:
        """
        End-to-end recommendation workflow:
          1. Resolve user profile securely (DB vs in-memory guest).
          2. Fetch candidates (Central + User's State).
          3. Pre-Filter deterministic eligibility (keep ELIGIBLE; queue POSSIBLY_ELIGIBLE; discard NOT_ELIGIBLE).
          4. Pre-Filter activity/deadline (keep OPEN; discard EXPIRED/NOT_YET_OPEN/INACTIVE).
          5. Multi-factor ranking (OpenAI structured output, with deterministic fallback).
          6. Assemble structured response.
        """
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        # 1. Resolve Profile Securely
        resolved_profile: UserProfileInput
        if user_id:
            db_profile = self.eligibility_service.get_user_profile_from_db(user_id)
            resolved_profile = db_profile if db_profile else UserProfileInput()
        else:
            resolved_profile = profile or UserProfileInput()

        # 2. Retrieve Candidate Schemes (Central + User State)
        candidate_schemes = self.get_candidate_schemes(resolved_profile)
        if not candidate_schemes:
            return RecommendationResponse(
                recommendations=[],
                verification_required=[],
                total_candidates=0,
                ranking_method="DETERMINISTIC_FALLBACK",
                query_used=query,
            )

        scheme_ids = [s["id"] for s in candidate_schemes if "id" in s]
        elig_rules_map = self.get_eligibility_rules_map(scheme_ids)

        # 3 & 4. Filter Pipeline: Eligibility and Registration Activity
        eligible_candidates: List[Tuple[Dict[str, Any], SchemeActivityInfo]] = []
        possibly_eligible_candidates: List[Tuple[Dict[str, Any], SchemeActivityInfo, List[str]]] = []

        for s in candidate_schemes:
            s_id = s["id"]
            rules = elig_rules_map.get(s_id, {})

            # Deterministic Eligibility Evaluation (Phase 3)
            elig_explanation: EligibilityExplanation = evaluate_eligibility(
                resolved_profile, s, rules
            )

            # Activity & Deadline Evaluation (Phase 4)
            activity_info: SchemeActivityInfo = get_scheme_activity(s)

            # Rule: Expired, Inactive, Not Yet Open, or Unknown schemes are NEVER recommended
            if not activity_info.is_actionable or activity_info.status != ActivityStatus.OPEN:
                continue

            if elig_explanation.status == EligibilityStatus.ELIGIBLE:
                eligible_candidates.append((s, activity_info))
            elif elig_explanation.status == EligibilityStatus.POSSIBLY_ELIGIBLE:
                # Collect criteria with UNKNOWN result
                missing = [
                    crit.criterion
                    for crit in elig_explanation.criteria
                    if crit.result == CriterionResult.UNKNOWN
                ]
                possibly_eligible_candidates.append((s, activity_info, missing))
            else:
                # NOT_ELIGIBLE -> strictly discarded
                continue

        total_candidates = len(eligible_candidates)
        if total_candidates == 0:
            # Process verification_required if any, but zero main recommendations
            verif_items = self._process_verification_items(
                possibly_eligible_candidates, resolved_profile, query
            )
            return RecommendationResponse(
                recommendations=[],
                verification_required=verif_items,
                total_candidates=0,
                ranking_method="DETERMINISTIC_FALLBACK",
                query_used=query,
            )

        # 5. Ranking Stage
        ranked_recommendations: List[RecommendationItem] = []
        ranking_method = "DETERMINISTIC_FALLBACK"

        # Attempt AI Ranking via OpenAI
        candidate_dicts = [item[0] for item in eligible_candidates]
        ai_result: Optional[AIRankingOutput] = None

        if self.openai_service.is_available():
            ai_result = self.openai_service.rank_schemes(
                candidate_schemes=candidate_dicts,
                profile=resolved_profile,
                query=query,
            )

        if ai_result and ai_result.ranked_schemes:
            ranking_method = "OPENAI"
            # Map of candidate scheme by ID
            candidate_map = {item[0]["id"]: item for item in eligible_candidates}
            ranked_ids: Set[str] = set()

            for ai_item in ai_result.ranked_schemes:
                if ai_item.scheme_id in candidate_map and ai_item.scheme_id not in ranked_ids:
                    s, act = candidate_map[ai_item.scheme_id]
                    ranked_ids.add(ai_item.scheme_id)

                    ranked_recommendations.append(
                        RecommendationItem(
                            scheme_id=s["id"],
                            scheme_name=s.get("scheme_name", ""),
                            eligibility_status=EligibilityStatus.ELIGIBLE,
                            relevance_score=ai_item.relevance_score,
                            relevance_reason=ai_item.reason,
                            activity_status=act.status,
                            deadline_status=act.deadline_status,
                            days_remaining=act.days_remaining,
                            benefits=s.get("benefits"),
                            official_url=s.get("official_url") or s.get("source_url"),
                            government_level=s.get("government_level"),
                            state_id=s.get("state_id"),
                        )
                    )

            # If AI omitted any candidates, supplement them using deterministic fallback
            for s, act in eligible_candidates:
                if s["id"] not in ranked_ids:
                    fb_score, fb_reason = DeterministicFallbackRanker.calculate_relevance(
                        s, resolved_profile, act, query
                    )
                    ranked_recommendations.append(
                        RecommendationItem(
                            scheme_id=s["id"],
                            scheme_name=s.get("scheme_name", ""),
                            eligibility_status=EligibilityStatus.ELIGIBLE,
                            relevance_score=fb_score,
                            relevance_reason=fb_reason,
                            activity_status=act.status,
                            deadline_status=act.deadline_status,
                            days_remaining=act.days_remaining,
                            benefits=s.get("benefits"),
                            official_url=s.get("official_url") or s.get("source_url"),
                            government_level=s.get("government_level"),
                            state_id=s.get("state_id"),
                        )
                    )
        else:
            # Deterministic Fallback Ranking for all candidates
            ranking_method = "DETERMINISTIC_FALLBACK"
            for s, act in eligible_candidates:
                fb_score, fb_reason = DeterministicFallbackRanker.calculate_relevance(
                    s, resolved_profile, act, query
                )
                ranked_recommendations.append(
                    RecommendationItem(
                        scheme_id=s["id"],
                        scheme_name=s.get("scheme_name", ""),
                        eligibility_status=EligibilityStatus.ELIGIBLE,
                        relevance_score=fb_score,
                        relevance_reason=fb_reason,
                        activity_status=act.status,
                        deadline_status=act.deadline_status,
                        days_remaining=act.days_remaining,
                        benefits=s.get("benefits"),
                        official_url=s.get("official_url") or s.get("source_url"),
                        government_level=s.get("government_level"),
                        state_id=s.get("state_id"),
                    )
                )

        # Sort recommendations descending by relevance_score
        ranked_recommendations.sort(key=lambda item: item.relevance_score, reverse=True)

        # Paginate recommendations
        paginated_recommendations = ranked_recommendations[offset : offset + limit]

        # Process Verification Required items
        verification_items = self._process_verification_items(
            possibly_eligible_candidates, resolved_profile, query
        )

        return RecommendationResponse(
            recommendations=paginated_recommendations,
            verification_required=verification_items,
            total_candidates=total_candidates,
            ranking_method=ranking_method,
            query_used=query,
        )

    def _process_verification_items(
        self,
        candidates: List[Tuple[Dict[str, Any], SchemeActivityInfo, List[str]]],
        profile: UserProfileInput,
        query: Optional[str] = None,
    ) -> List[VerificationRequiredItem]:
        """Rank and format POSSIBLY_ELIGIBLE active schemes separately."""
        items: List[VerificationRequiredItem] = []
        for s, act, missing in candidates:
            fb_score, fb_reason = DeterministicFallbackRanker.calculate_relevance(
                s, profile, act, query
            )
            items.append(
                VerificationRequiredItem(
                    scheme_id=s["id"],
                    scheme_name=s.get("scheme_name", ""),
                    eligibility_status=EligibilityStatus.POSSIBLY_ELIGIBLE,
                    status_label="Eligibility needs verification",
                    relevance_score=fb_score,
                    relevance_reason=fb_reason,
                    activity_status=act.status,
                    deadline_status=act.deadline_status,
                    days_remaining=act.days_remaining,
                    benefits=s.get("benefits"),
                    official_url=s.get("official_url") or s.get("source_url"),
                    government_level=s.get("government_level"),
                    state_id=s.get("state_id"),
                    missing_criteria=missing,
                )
            )
        items.sort(key=lambda x: x.relevance_score, reverse=True)
        return items


def recommend_schemes(
    profile: Optional[UserProfileInput] = None,
    user_id: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> RecommendationResponse:
    """Convenience functional wrapper for recommendation service."""
    service = RecommendationService()
    return service.recommend_schemes(
        profile=profile,
        user_id=user_id,
        query=query,
        limit=limit,
        offset=offset,
    )
