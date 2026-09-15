"""
Unit and Integration Tests: AI Recommendation Engine (Phase 5)
--------------------------------------------------------------
Comprehensive test matrix for:
  - Pre-filtering (eligibility & activity)
  - Geographic filtering (Central vs State)
  - Relevance match score properties (0-100, independent of eligibility)
  - Deterministic fallback ranking & explainability
  - OpenAI integration mocking, validation, and safety
  - Authentication security & cross-user isolation
  - Natural-language query influences
  - Deadline urgency weighting
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import jwt
from fastapi.testclient import TestClient
from app.main import app
from app.models.deadline import ActivityStatus, DeadlineClassification, SchemeActivityInfo
from app.models.eligibility import EligibilityStatus, UserProfileInput
from app.models.recommendation import (
    AIRankedItem,
    AIRankingOutput,
    RecommendationRequest,
    RecommendationResponse,
)
from app.integrations.openai_service import OpenAIService
from app.services.recommendation_engine import (
    DeterministicFallbackRanker,
    RecommendationService,
)


class TestPreFiltering(unittest.TestCase):
    """Tests confirming strict pre-filtering before ranking."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_openai = MagicMock(spec=OpenAIService)
        self.mock_openai.is_available.return_value = False  # Use fallback for predictable testing
        self.service = RecommendationService(
            openai_service=self.mock_openai,
            client=self.mock_client,
        )

    @patch("app.services.recommendation_engine.get_scheme_activity")
    @patch("app.services.recommendation_engine.evaluate_eligibility")
    def test_pre_filtering_eligibility_and_activity(self, mock_eval, mock_act):
        """
        Verify:
          - NOT_ELIGIBLE schemes are discarded
          - POSSIBLY_ELIGIBLE schemes go to verification_required
          - ELIGIBLE + OPEN schemes are in main recommendations
          - EXPIRED, INACTIVE, NOT_YET_OPEN schemes are discarded
        """
        # Create 5 test schemes
        schemes = [
            {"id": "11111111-1111-1111-1111-111111111111", "scheme_name": "Scheme 1: Eligible & Open", "government_level": "CENTRAL"},
            {"id": "22222222-2222-2222-2222-222222222222", "scheme_name": "Scheme 2: Not Eligible", "government_level": "CENTRAL"},
            {"id": "33333333-3333-3333-3333-333333333333", "scheme_name": "Scheme 3: Possibly Eligible & Open", "government_level": "CENTRAL"},
            {"id": "44444444-4444-4444-4444-444444444444", "scheme_name": "Scheme 4: Eligible but Expired", "government_level": "CENTRAL"},
            {"id": "55555555-5555-5555-5555-555555555555", "scheme_name": "Scheme 5: Eligible but Inactive", "government_level": "CENTRAL"},
        ]

        # Setup mocks
        self.service.get_candidate_schemes = MagicMock(return_value=schemes)
        self.service.get_eligibility_rules_map = MagicMock(return_value={})

        # Eligibility mock setup
        def fake_eval(profile, scheme, rules):
            s_id = scheme["id"]
            mock_res = MagicMock()
            if s_id in ("11111111-1111-1111-1111-111111111111", "44444444-4444-4444-4444-444444444444", "55555555-5555-5555-5555-555555555555"):
                mock_res.status = EligibilityStatus.ELIGIBLE
            elif s_id == "33333333-3333-3333-3333-333333333333":
                mock_res.status = EligibilityStatus.POSSIBLY_ELIGIBLE
                mock_res.criteria = []
            else:
                mock_res.status = EligibilityStatus.NOT_ELIGIBLE
            return mock_res

        mock_eval.side_effect = fake_eval

        # Activity mock setup
        def fake_activity(scheme):
            s_id = scheme["id"]
            if s_id in ("11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333"):
                return SchemeActivityInfo(
                    status=ActivityStatus.OPEN,
                    deadline_status=DeadlineClassification.MORE_THAN_15_DAYS,
                    days_remaining=20,
                    is_actionable=True,
                    reason="Open",
                )
            elif s_id == "44444444-4444-4444-4444-444444444444":
                return SchemeActivityInfo(
                    status=ActivityStatus.EXPIRED,
                    deadline_status=DeadlineClassification.EXPIRED,
                    days_remaining=-2,
                    is_actionable=False,
                    reason="Expired",
                )
            else:
                return SchemeActivityInfo(
                    status=ActivityStatus.INACTIVE,
                    deadline_status=DeadlineClassification.NO_DEADLINE,
                    days_remaining=None,
                    is_actionable=False,
                    reason="Inactive",
                )

        mock_act.side_effect = fake_activity

        profile = UserProfileInput(age=30)
        res = self.service.recommend_schemes(profile=profile)

        # Only Scheme 1 should be in main recommendations
        self.assertEqual(len(res.recommendations), 1)
        self.assertEqual(res.recommendations[0].scheme_id, "11111111-1111-1111-1111-111111111111")
        self.assertEqual(res.recommendations[0].eligibility_status, EligibilityStatus.ELIGIBLE)
        self.assertEqual(res.recommendations[0].activity_status, ActivityStatus.OPEN)

        # Scheme 3 (Possibly Eligible) should be in verification_required
        self.assertEqual(len(res.verification_required), 1)
        self.assertEqual(res.verification_required[0].scheme_id, "33333333-3333-3333-3333-333333333333")
        self.assertEqual(res.verification_required[0].eligibility_status, EligibilityStatus.POSSIBLY_ELIGIBLE)


class TestGeographicFiltering(unittest.TestCase):
    """Tests for Central vs State candidate inclusion."""

    def test_candidate_schemes_central_and_user_state_only(self):
        """Verify candidate schemes fetch Central + User's state, excluding other states."""
        mock_client = MagicMock()
        service = RecommendationService(client=mock_client)

        central_mock = MagicMock()
        central_mock.data = [{"id": "c1", "government_level": "CENTRAL"}]

        state_mock = MagicMock()
        state_mock.data = [{"id": "s1", "government_level": "STATE", "state_id": 10}]

        # Setup table calls
        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "schemes":
                def select_mock(*args, **kwargs):
                    mock_sel = MagicMock()
                    def eq_mock(col, val):
                        mock_eq = MagicMock()
                        if col == "government_level" and val == "CENTRAL":
                            mock_eq.execute.return_value = central_mock
                        elif col == "government_level" and val == "STATE":
                            def eq_state(col2, val2):
                                mock_state = MagicMock()
                                mock_state.execute.return_value = state_mock
                                return mock_state
                            mock_eq.eq = eq_state
                        return mock_eq
                    mock_sel.eq = eq_mock
                    return mock_sel
                mock_table.select = select_mock
            return mock_table

        mock_client.table.side_effect = table_side_effect

        profile = UserProfileInput(state_id=10)
        candidates = service.get_candidate_schemes(profile)

        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["id"], "c1")
        self.assertEqual(candidates[1]["id"], "s1")


class TestRelevanceScoreProperties(unittest.TestCase):
    """Tests confirming relevance score is bounded [0, 100] and does not alter eligibility."""

    def test_score_bounded_and_distinct_from_eligibility(self):
        scheme = {
            "id": "test-id",
            "scheme_name": "Farmer Assistance",
            "description": "Financial subsidy for agriculture",
            "benefits": "Cash support",
            "government_level": "CENTRAL",
        }
        profile = UserProfileInput(occupation="Farmer")
        act = SchemeActivityInfo(
            status=ActivityStatus.OPEN,
            deadline_status=DeadlineClassification.URGENT,
            days_remaining=2,
            is_actionable=True,
            reason="Urgent",
        )

        score, reason = DeterministicFallbackRanker.calculate_relevance(
            scheme=scheme, profile=profile, activity=act, query="farmer cash subsidy"
        )

        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertIn("Farmer", reason)
        self.assertIn("urgent", reason.lower())


class TestOpenAIServiceValidation(unittest.TestCase):
    """Tests validating OpenAI output handling, sanitization, and fallback."""

    def test_openai_unavailable_falls_back(self):
        """OpenAIService returns None when API key is missing."""
        service = OpenAIService(api_key=None)
        self.assertFalse(service.is_available())
        result = service.rank_schemes([], UserProfileInput())
        self.assertIsNone(result)

    def test_openai_data_minimization(self):
        """Verify prepare_sanitized_user_context strips sensitive attributes."""
        service = OpenAIService(api_key="test-key")
        profile = UserProfileInput(
            user_id="secret-user-uuid",
            age=35,
            state_name="Tamil Nadu",
            occupation="Teacher",
            family_details={"private_notes": "sensitive info"},
        )
        context = service.prepare_sanitized_user_context(profile, query="scholarship")

        self.assertNotIn("user_id", context)
        self.assertNotIn("secret-user-uuid", str(context))
        self.assertNotIn("family_details", context)
        self.assertEqual(context["occupation"], "Teacher")
        self.assertEqual(context["citizen_expressed_need"], "scholarship")

    def test_openai_discards_unknown_scheme_id(self):
        """Verify hallucinated scheme IDs not in candidate set are discarded."""
        service = OpenAIService(api_key="test-key")
        service.is_available = MagicMock(return_value=True)

        mock_openai_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = (
            '{"ranked_schemes": ['
            '  {"scheme_id": "valid-id", "relevance_score": 90, "reason": "Good match"},'
            '  {"scheme_id": "hallucinated-fake-id", "relevance_score": 99, "reason": "Invented"}'
            ']}'
        )
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
        service._client = mock_openai_client

        candidates = [{"id": "valid-id", "scheme_name": "Valid Scheme"}]
        result = service.rank_schemes(candidates, UserProfileInput())

        self.assertIsNotNone(result)
        self.assertEqual(len(result.ranked_schemes), 1)
        self.assertEqual(result.ranked_schemes[0].scheme_id, "valid-id")
        self.assertEqual(result.ranked_schemes[0].relevance_score, 90)

    def test_openai_clamps_invalid_scores(self):
        """Verify scores outside 0-100 are clamped safely."""
        service = OpenAIService(api_key="test-key")
        service.is_available = MagicMock(return_value=True)

        mock_openai_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = (
            '{"ranked_schemes": ['
            '  {"scheme_id": "s1", "relevance_score": 150, "reason": "Too high"},'
            '  {"scheme_id": "s2", "relevance_score": -20, "reason": "Negative"}'
            ']}'
        )
        mock_openai_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
        service._client = mock_openai_client

        candidates = [
            {"id": "s1", "scheme_name": "S1"},
            {"id": "s2", "scheme_name": "S2"},
        ]
        result = service.rank_schemes(candidates, UserProfileInput())

        self.assertEqual(result.ranked_schemes[0].relevance_score, 100)
        self.assertEqual(result.ranked_schemes[1].relevance_score, 0)

    def test_openai_failure_returns_none_safely(self):
        """Verify exceptions during API call gracefully return None without raising 500."""
        service = OpenAIService(api_key="test-key")
        service.is_available = MagicMock(return_value=True)

        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.side_effect = Exception("API Timeout / Rate Limit")
        service._client = mock_openai_client

        candidates = [{"id": "s1", "scheme_name": "S1"}]
        result = service.rank_schemes(candidates, UserProfileInput())
        self.assertIsNone(result)


class TestRecommendationAPI(unittest.TestCase):
    """Integration tests for /api/recommendations endpoints and security rules."""

    def setUp(self):
        self.client = TestClient(app)
        self.user_a_id = "11111111-1111-1111-1111-111111111111"
        self.user_b_id = "22222222-2222-2222-2222-222222222222"
        self.test_secret = "super-secret-test-key-minimum-32-chars-long!"
        self.token_user_a = jwt.encode(
            {"sub": self.user_a_id, "role": "authenticated"},
            self.test_secret,
            algorithm="HS256",
        )
        self.token_user_b = jwt.encode(
            {"sub": self.user_b_id, "role": "authenticated"},
            self.test_secret,
            algorithm="HS256",
        )

    @patch("app.routes.recommendation_routes.recommendation_service.recommend_schemes")
    def test_post_recommendations_guest_success(self, mock_rec):
        """Guest user can retrieve recommendations via in-memory profile."""
        mock_rec.return_value = RecommendationResponse(
            recommendations=[
                {
                    "scheme_id": "11111111-1111-1111-1111-111111111111",
                    "scheme_name": "National Scholarship",
                    "eligibility_status": "ELIGIBLE",
                    "relevance_score": 92,
                    "relevance_reason": "Matches student profile",
                    "activity_status": "OPEN",
                    "deadline_status": "APPROACHING",
                    "days_remaining": 10,
                }
            ],
            verification_required=[],
            total_candidates=1,
            ranking_method="DETERMINISTIC_FALLBACK",
            query_used="scholarship for college",
        )

        payload = {
            "query": "scholarship for college",
            "profile": {
                "age": 20,
                "occupation": "Student",
            },
        }
        response = self.client.post("/api/recommendations", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["recommendations"]), 1)
        self.assertEqual(data["recommendations"][0]["relevance_score"], 92)
        self.assertEqual(data["recommendations"][0]["eligibility_status"], "ELIGIBLE")

    def test_guest_cannot_pass_user_id(self):
        """Guest cannot request private database profiles using user_id -> 401."""
        payload = {
            "user_id": "11111111-1111-1111-1111-111111111111",
            "query": "farming subsidy",
        }
        response = self.client.post("/api/recommendations", json=payload)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Guest/anonymous requests cannot access private user profiles", response.json()["detail"])

    def test_authenticated_cross_user_access_blocked(self):
        """Authenticated user A cannot supply user B's user_id -> 403."""
        headers = {"Authorization": f"Bearer {self.token_user_a}"}
        payload = {
            "user_id": self.user_b_id,
            "query": "scholarship",
        }
        response = self.client.post("/api/recommendations", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Cross-user access denied", response.json()["detail"])

    def test_authenticated_profile_override_blocked(self):
        """Authenticated user cannot override database profile with client dictionary -> 400."""
        headers = {"Authorization": f"Bearer {self.token_user_a}"}
        payload = {
            "user_id": self.user_a_id,
            "profile": {
                "age": 45,
                "occupation": "Overridden Occupation",
            },
        }
        response = self.client.post("/api/recommendations", json=payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Authenticated users cannot override their database profile", response.json()["detail"])

    def test_authenticated_get_profile_override_blocked(self):
        """Authenticated user cannot override database profile via GET query params -> 400."""
        headers = {"Authorization": f"Bearer {self.token_user_a}"}
        response = self.client.get("/api/recommendations?age=45", headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Authenticated users cannot override their database profile", response.json()["detail"])

    @patch("app.routes.recommendation_routes.recommendation_service.recommend_schemes")
    def test_get_recommendations_endpoint(self, mock_rec):
        """GET /api/recommendations returns formatted recommendations."""
        mock_rec.return_value = RecommendationResponse(
            recommendations=[],
            verification_required=[],
            total_candidates=0,
            ranking_method="DETERMINISTIC_FALLBACK",
            query_used="pension",
        )
        response = self.client.get("/api/recommendations?q=pension&age=65")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["ranking_method"], "DETERMINISTIC_FALLBACK")


class TestAIRankingIntegration(unittest.TestCase):
    """Tests confirming OpenAI integration and candidate handling in service."""

    @patch("app.services.recommendation_engine.get_scheme_activity")
    @patch("app.services.recommendation_engine.evaluate_eligibility")
    def test_openai_ranking_success(self, mock_eval, mock_act):
        """When OpenAI returns structured rankings, they are applied and sorted."""
        mock_openai = MagicMock(spec=OpenAIService)
        mock_openai.is_available.return_value = True

        # AI returns structured output ranking s2 higher than s1
        mock_openai.rank_schemes.return_value = AIRankingOutput(
            ranked_schemes=[
                AIRankedItem(scheme_id="s2", relevance_score=95, reason="Matches expressed need strongly"),
                AIRankedItem(scheme_id="s1", relevance_score=70, reason="General match"),
            ]
        )

        service = RecommendationService(openai_service=mock_openai)
        service.get_candidate_schemes = MagicMock(
            return_value=[
                {"id": "s1", "scheme_name": "Scheme 1"},
                {"id": "s2", "scheme_name": "Scheme 2"},
            ]
        )
        service.get_eligibility_rules_map = MagicMock(return_value={})

        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        mock_act.return_value = SchemeActivityInfo(
            status=ActivityStatus.OPEN,
            deadline_status=DeadlineClassification.MORE_THAN_15_DAYS,
            days_remaining=25,
            is_actionable=True,
            reason="Open",
        )

        res = service.recommend_schemes(profile=UserProfileInput(age=28), query="special need")

        self.assertEqual(res.ranking_method, "OPENAI")
        self.assertEqual(len(res.recommendations), 2)
        # s2 should be first because relevance_score=95 > 70
        self.assertEqual(res.recommendations[0].scheme_id, "s2")
        self.assertEqual(res.recommendations[0].relevance_score, 95)
        self.assertEqual(res.recommendations[1].scheme_id, "s1")
        self.assertEqual(res.recommendations[1].relevance_score, 70)

    @patch("app.services.recommendation_engine.get_scheme_activity")
    @patch("app.services.recommendation_engine.evaluate_eligibility")
    def test_openai_ranking_supplements_omitted_candidates(self, mock_eval, mock_act):
        """When OpenAI ranks s1 but omits s2, s2 is preserved via fallback ranking."""
        mock_openai = MagicMock(spec=OpenAIService)
        mock_openai.is_available.return_value = True

        # AI omitted s2
        mock_openai.rank_schemes.return_value = AIRankingOutput(
            ranked_schemes=[
                AIRankedItem(scheme_id="s1", relevance_score=85, reason="Direct AI match"),
            ]
        )

        service = RecommendationService(openai_service=mock_openai)
        service.get_candidate_schemes = MagicMock(
            return_value=[
                {"id": "s1", "scheme_name": "Scheme 1"},
                {"id": "s2", "scheme_name": "Scheme 2"},
            ]
        )
        service.get_eligibility_rules_map = MagicMock(return_value={})

        mock_eval.return_value = MagicMock(status=EligibilityStatus.ELIGIBLE)
        mock_act.return_value = SchemeActivityInfo(
            status=ActivityStatus.OPEN,
            deadline_status=DeadlineClassification.NO_DEADLINE,
            days_remaining=None,
            is_actionable=True,
            reason="Open",
        )

        res = service.recommend_schemes(profile=UserProfileInput(age=28))

        self.assertEqual(res.ranking_method, "OPENAI")
        self.assertEqual(len(res.recommendations), 2)
        ids = [item.scheme_id for item in res.recommendations]
        self.assertIn("s1", ids)
        self.assertIn("s2", ids)


class TestQueryAndDeadlineInfluence(unittest.TestCase):
    """Tests confirming query keywords and deadline urgency influence ranking scores."""

    def test_query_boosts_matching_scheme(self):
        """Query matching keywords increases relevance match score."""
        scheme = {
            "id": "s-farmer",
            "scheme_name": "Kisan Credit Loan Program",
            "description": "Financial assistance for crop seeds and agriculture fertilizers",
            "benefits": "Low interest credit support",
            "government_level": "CENTRAL",
        }
        profile = UserProfileInput(occupation="Teacher")  # Occupation not matching
        act = SchemeActivityInfo(
            status=ActivityStatus.OPEN,
            deadline_status=DeadlineClassification.NO_DEADLINE,
            days_remaining=None,
            is_actionable=True,
            reason="Open",
        )

        # Score without query
        score_no_query, _ = DeterministicFallbackRanker.calculate_relevance(
            scheme=scheme, profile=profile, activity=act, query=None
        )

        # Score with matching query
        score_with_query, reason = DeterministicFallbackRanker.calculate_relevance(
            scheme=scheme, profile=profile, activity=act, query="crop fertilizers"
        )

        self.assertGreater(score_with_query, score_no_query)
        self.assertIn("fertilizers", reason)

    def test_deadline_urgency_boosts_score(self):
        """Approaching deadline gives higher urgency weighting than rolling deadline."""
        scheme = {
            "id": "s-generic",
            "scheme_name": "General Assistance",
            "description": "General program",
            "government_level": "CENTRAL",
        }
        profile = UserProfileInput()

        act_today = SchemeActivityInfo(
            status=ActivityStatus.OPEN,
            deadline_status=DeadlineClassification.CLOSING_TODAY,
            days_remaining=0,
            is_actionable=True,
            reason="Closing today",
        )
        act_none = SchemeActivityInfo(
            status=ActivityStatus.OPEN,
            deadline_status=DeadlineClassification.NO_DEADLINE,
            days_remaining=None,
            is_actionable=True,
            reason="Open-ended",
        )

        score_today, reason_today = DeterministicFallbackRanker.calculate_relevance(
            scheme=scheme, profile=profile, activity=act_today
        )
        score_none, _ = DeterministicFallbackRanker.calculate_relevance(
            scheme=scheme, profile=profile, activity=act_none
        )

        self.assertGreater(score_today, score_none)
        self.assertIn("immediate action required", reason_today.lower())

    @patch("app.services.recommendation_engine.get_scheme_activity")
    @patch("app.services.recommendation_engine.evaluate_eligibility")
    def test_query_cannot_override_eligibility(self, mock_eval, mock_act):
        """Natural language query with exact keywords CANNOT make an ineligible scheme appear."""
        mock_openai = MagicMock(spec=OpenAIService)
        mock_openai.is_available.return_value = False

        service = RecommendationService(openai_service=mock_openai)
        service.get_candidate_schemes = MagicMock(
            return_value=[
                {"id": "s-ineligible", "scheme_name": "Farmer Grant Exact Match"},
            ]
        )
        service.get_eligibility_rules_map = MagicMock(return_value={})

        # Deterministic engine declares NOT_ELIGIBLE
        mock_eval.return_value = MagicMock(status=EligibilityStatus.NOT_ELIGIBLE)
        mock_act.return_value = SchemeActivityInfo(
            status=ActivityStatus.OPEN,
            deadline_status=DeadlineClassification.MORE_THAN_15_DAYS,
            days_remaining=30,
            is_actionable=True,
            reason="Open",
        )

        res = service.recommend_schemes(
            profile=UserProfileInput(age=20),
            query="Farmer Grant Exact Match",
        )

        self.assertEqual(len(res.recommendations), 0)
        self.assertEqual(res.total_candidates, 0)


if __name__ == "__main__":
    unittest.main()

