"""
Comprehensive Unit & Integration Tests: Deterministic Eligibility Engine
-------------------------------------------------------------------------
Tests all deterministic criteria logic:
  - Age (valid, below min, above max, missing)
  - Income (below max, above max, missing)
  - Gender (matching, mismatching, missing, ANY/ALL)
  - Occupation (matching, mismatching, missing, casing normalization)
  - Education (hierarchy comparison: sufficient, insufficient, missing)
  - Category (matching, mismatching, missing, alias normalization)
  - Disability (required + true, required + false, required + unknown, not required)
  - State (matching, mismatching, missing, Central scheme Pan-India)
  - District (matching, mismatching, missing)
  - Combined rules (all pass => ELIGIBLE, 1 fail => NOT_ELIGIBLE, unknown => POSSIBLY_ELIGIBLE)
  - Other conditions (supported marital_status/bpl/landholding, unsupported => UNKNOWN)
  - Explanations structure & reasons
  - Eligibility API endpoints (POST /evaluate, GET /schemes)
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import jwt

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.models.eligibility import (
    CriterionResult,
    EligibilityStatus,
    UserProfileInput,
)
from app.services.eligibility_engine import (
    DeterministicEligibilityEngine,
    evaluate_eligibility,
)


class TestEligibilityEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DeterministicEligibilityEngine()
        self.base_scheme = {
            "id": "11111111-1111-1111-1111-111111111111",
            "scheme_name": "Test Welfare Scheme",
            "government_level": "CENTRAL",
            "state_id": None,
        }

    # ==========================================
    # 1. AGE TESTS
    # ==========================================
    def test_age_valid(self):
        """Age within [min, max] passes."""
        res = self.engine.evaluate_age(user_age=25, min_age=18, max_age=40)
        self.assertIsNotNone(res)
        self.assertEqual(res.result, CriterionResult.PASS)
        self.assertIn("satisfies", res.reason)

    def test_age_below_min(self):
        """Age below min_age fails."""
        res = self.engine.evaluate_age(user_age=16, min_age=18, max_age=40)
        self.assertEqual(res.result, CriterionResult.FAIL)
        self.assertIn("below the minimum", res.reason)

    def test_age_above_max(self):
        """Age above max_age fails."""
        res = self.engine.evaluate_age(user_age=45, min_age=18, max_age=40)
        self.assertEqual(res.result, CriterionResult.FAIL)
        self.assertIn("exceeds the maximum", res.reason)

    def test_age_missing(self):
        """Missing age produces UNKNOWN."""
        res = self.engine.evaluate_age(user_age=None, min_age=18, max_age=40)
        self.assertEqual(res.result, CriterionResult.UNKNOWN)
        self.assertIn("unknown", res.reason)

    def test_age_no_restriction(self):
        """No age bounds returns None (not evaluated)."""
        res = self.engine.evaluate_age(user_age=25, min_age=None, max_age=None)
        self.assertIsNone(res)

    # ==========================================
    # 2. INCOME TESTS
    # ==========================================
    def test_income_below_max(self):
        """Income <= max_income passes."""
        res = self.engine.evaluate_income(user_income=150000.0, max_income=250000.0)
        self.assertEqual(res.result, CriterionResult.PASS)

    def test_income_above_max(self):
        """Income > max_income fails."""
        res = self.engine.evaluate_income(user_income=300000.0, max_income=250000.0)
        self.assertEqual(res.result, CriterionResult.FAIL)
        self.assertIn("exceeds", res.reason)

    def test_income_missing(self):
        """Missing income produces UNKNOWN."""
        res = self.engine.evaluate_income(user_income=None, max_income=250000.0)
        self.assertEqual(res.result, CriterionResult.UNKNOWN)

    # ==========================================
    # 3. GENDER TESTS
    # ==========================================
    def test_gender_matching(self):
        """Matching gender passes."""
        res = self.engine.evaluate_gender(user_gender="FEMALE", scheme_gender="FEMALE")
        self.assertEqual(res.result, CriterionResult.PASS)

    def test_gender_mismatching(self):
        """Mismatching gender fails."""
        res = self.engine.evaluate_gender(user_gender="MALE", scheme_gender="FEMALE")
        self.assertEqual(res.result, CriterionResult.FAIL)

    def test_gender_missing(self):
        """Missing user gender produces UNKNOWN."""
        res = self.engine.evaluate_gender(user_gender=None, scheme_gender="FEMALE")
        self.assertEqual(res.result, CriterionResult.UNKNOWN)

    def test_gender_all_or_none(self):
        """Scheme gender ALL/ANY/None returns None (not restricted)."""
        self.assertIsNone(self.engine.evaluate_gender("MALE", "ALL"))
        self.assertIsNone(self.engine.evaluate_gender("FEMALE", None))

    # ==========================================
    # 4. OCCUPATION TESTS
    # ==========================================
    def test_occupation_matching(self):
        """Matching occupation passes."""
        res = self.engine.evaluate_occupation(user_occ="Farmer", scheme_occ="Farmer")
        self.assertEqual(res.result, CriterionResult.PASS)

    def test_occupation_capitalization_normalization(self):
        """Case insensitive match passes."""
        res = self.engine.evaluate_occupation(user_occ="FARMER", scheme_occ="farmer")
        self.assertEqual(res.result, CriterionResult.PASS)

    def test_occupation_mismatching(self):
        """Mismatching occupation fails."""
        res = self.engine.evaluate_occupation(user_occ="Software Engineer", scheme_occ="Farmer")
        self.assertEqual(res.result, CriterionResult.FAIL)

    def test_occupation_missing(self):
        """Missing occupation produces UNKNOWN."""
        res = self.engine.evaluate_occupation(user_occ=None, scheme_occ="Farmer")
        self.assertEqual(res.result, CriterionResult.UNKNOWN)

    # ==========================================
    # 5. EDUCATION TESTS
    # ==========================================
    def test_education_sufficient(self):
        """Higher education meets or exceeds required tier."""
        res = self.engine.evaluate_education(user_edu="Postgraduate", scheme_edu="Graduate")
        self.assertEqual(res.result, CriterionResult.PASS)

    def test_education_insufficient(self):
        """Lower education fails required higher tier."""
        res = self.engine.evaluate_education(user_edu="Primary", scheme_edu="Graduate")
        self.assertEqual(res.result, CriterionResult.FAIL)
        self.assertIn("below the required threshold", res.reason)

    def test_education_missing(self):
        """Missing user education produces UNKNOWN."""
        res = self.engine.evaluate_education(user_edu=None, scheme_edu="10th")
        self.assertEqual(res.result, CriterionResult.UNKNOWN)

    # ==========================================
    # 6. CATEGORY TESTS
    # ==========================================
    def test_category_matching(self):
        """Matching social category passes."""
        res = self.engine.evaluate_category(user_cat="SC", scheme_cat="SC")
        self.assertEqual(res.result, CriterionResult.PASS)

    def test_category_alias_normalization(self):
        """Full category name matches alias (e.g. Scheduled Caste -> SC)."""
        res = self.engine.evaluate_category(user_cat="Scheduled Caste", scheme_cat="SC, ST")
        self.assertEqual(res.result, CriterionResult.PASS)

    def test_category_mismatching(self):
        """Mismatching category fails."""
        res = self.engine.evaluate_category(user_cat="GENERAL", scheme_cat="SC, ST")
        self.assertEqual(res.result, CriterionResult.FAIL)

    def test_category_missing(self):
        """Missing user category produces UNKNOWN."""
        res = self.engine.evaluate_category(user_cat=None, scheme_cat="OBC")
        self.assertEqual(res.result, CriterionResult.UNKNOWN)

    # ==========================================
    # 7. DISABILITY TESTS
    # ==========================================
    def test_disability_required_true(self):
        """Required disability + user disability true passes."""
        res = self.engine.evaluate_disability(user_disability=True, disability_required=True)
        self.assertEqual(res.result, CriterionResult.PASS)

    def test_disability_required_false(self):
        """Required disability + user disability false fails."""
        res = self.engine.evaluate_disability(user_disability=False, disability_required=True)
        self.assertEqual(res.result, CriterionResult.FAIL)

    def test_disability_required_unknown(self):
        """Required disability + user disability None produces UNKNOWN."""
        res = self.engine.evaluate_disability(user_disability=None, disability_required=True)
        self.assertEqual(res.result, CriterionResult.UNKNOWN)

    def test_disability_not_required(self):
        """When not required, returns None (not evaluated as constraint)."""
        res = self.engine.evaluate_disability(user_disability=False, disability_required=False)
        self.assertIsNone(res)

    # ==========================================
    # 8. STATE TESTS
    # ==========================================
    def test_state_central_scheme_pan_india(self):
        """Central schemes without state_restriction pass for any citizen."""
        res = self.engine.evaluate_state(
            user_state_id=23,
            government_level="CENTRAL",
            scheme_state_id=None,
            state_restriction=None,
        )
        self.assertEqual(res.result, CriterionResult.PASS)
        self.assertIn("Pan-India", res.reason)

    def test_state_matching_state_scheme(self):
        """State scheme matching user state passes."""
        res = self.engine.evaluate_state(
            user_state_id=23,
            government_level="STATE",
            scheme_state_id=23,
            state_restriction=None,
        )
        self.assertEqual(res.result, CriterionResult.PASS)

    def test_state_mismatching_state_scheme(self):
        """State scheme mismatching user state fails."""
        res = self.engine.evaluate_state(
            user_state_id=4,  # Delhi
            government_level="STATE",
            scheme_state_id=23,  # Tamil Nadu
            state_restriction=None,
        )
        self.assertEqual(res.result, CriterionResult.FAIL)

    def test_state_missing_state_scheme(self):
        """Missing user state for State scheme produces UNKNOWN."""
        res = self.engine.evaluate_state(
            user_state_id=None,
            government_level="STATE",
            scheme_state_id=23,
            state_restriction=None,
        )
        self.assertEqual(res.result, CriterionResult.UNKNOWN)

    # ==========================================
    # 9. DISTRICT TESTS
    # ==========================================
    def test_district_matching(self):
        """Matching district passes."""
        res = self.engine.evaluate_district(user_district_id=1, district_restriction=1)
        self.assertEqual(res.result, CriterionResult.PASS)

    def test_district_mismatching(self):
        """Mismatching district fails."""
        res = self.engine.evaluate_district(user_district_id=2, district_restriction=1)
        self.assertEqual(res.result, CriterionResult.FAIL)

    def test_district_missing(self):
        """Missing user district produces UNKNOWN."""
        res = self.engine.evaluate_district(user_district_id=None, district_restriction=1)
        self.assertEqual(res.result, CriterionResult.UNKNOWN)

    def test_district_no_restriction(self):
        """No district restriction returns None."""
        self.assertIsNone(self.engine.evaluate_district(user_district_id=1, district_restriction=None))

    # ==========================================
    # 10. OTHER CONDITIONS TESTS
    # ==========================================
    def test_other_conditions_supported(self):
        """Supported other conditions (marital_status, bpl_card, landholding)."""
        family = {
            "marital_status": "MARRIED",
            "bpl_card": True,
            "landholding_hectares": 1.5,
        }
        conditions = {
            "marital_status": "MARRIED",
            "bpl_card": True,
            "max_landholding_hectares": 2.0,
        }
        evals = self.engine.evaluate_other_conditions(family, conditions)
        self.assertEqual(len(evals), 3)
        self.assertTrue(all(e.result == CriterionResult.PASS for e in evals))

    def test_other_conditions_unsupported_yields_unknown(self):
        """Unsupported structured condition yields UNKNOWN without guessing."""
        conditions = {"custom_unsupported_criteria_xyz": "special_val"}
        evals = self.engine.evaluate_other_conditions({}, conditions)
        self.assertEqual(len(evals), 1)
        self.assertEqual(evals[0].result, CriterionResult.UNKNOWN)
        self.assertIn("unsupported or unmodeled structure", evals[0].reason)

    # ==========================================
    # 11. COMBINED THREE-STATE DECISION RULES
    # ==========================================
    def test_combined_all_pass_yields_eligible(self):
        """All criteria PASS => ELIGIBLE (🟢)."""
        profile = UserProfileInput(
            age=25,
            annual_income=150000.0,
            gender="FEMALE",
            occupation="Farmer",
            state_id=23,
        )
        scheme = {"government_level": "STATE", "state_id": 23}
        rules = {
            "min_age": 18,
            "max_age": 40,
            "max_income": 250000.0,
            "gender": "FEMALE",
            "occupation": "Farmer",
        }
        res = evaluate_eligibility(profile, scheme, rules)
        self.assertEqual(res.status, EligibilityStatus.ELIGIBLE)
        self.assertEqual(res.display_status, "🟢 Eligible")
        self.assertEqual(res.failed_criteria_count, 0)
        self.assertEqual(res.unknown_criteria_count, 0)
        self.assertIn("fully satisfied", res.summary)

    def test_combined_one_fail_yields_not_eligible(self):
        """One mandatory failure => NOT_ELIGIBLE (🔴), even if other rules pass."""
        profile = UserProfileInput(
            age=50,  # Fails max_age
            annual_income=100000.0,  # Passes
            gender="FEMALE",  # Passes
        )
        scheme = {"government_level": "CENTRAL"}
        rules = {"max_age": 40, "max_income": 250000.0, "gender": "FEMALE"}
        res = evaluate_eligibility(profile, scheme, rules)
        self.assertEqual(res.status, EligibilityStatus.NOT_ELIGIBLE)
        self.assertEqual(res.display_status, "🔴 Not Eligible")
        self.assertEqual(res.failed_criteria_count, 1)
        self.assertIn("'age'", res.summary)

    def test_combined_no_fail_with_unknown_yields_possibly_eligible(self):
        """Passes known criteria + missing required data => POSSIBLY_ELIGIBLE (🟡)."""
        profile = UserProfileInput(
            age=25,  # Passes
            annual_income=None,  # Unknown
            gender="FEMALE",  # Passes
        )
        scheme = {"government_level": "CENTRAL"}
        rules = {"min_age": 18, "max_income": 250000.0, "gender": "FEMALE"}
        res = evaluate_eligibility(profile, scheme, rules)
        self.assertEqual(res.status, EligibilityStatus.POSSIBLY_ELIGIBLE)
        self.assertEqual(res.display_status, "🟡 Possibly Eligible")
        self.assertEqual(res.failed_criteria_count, 0)
        self.assertEqual(res.unknown_criteria_count, 1)
        self.assertIn("'annual_income'", res.summary)

    def test_combined_multiple_failures_yields_not_eligible(self):
        """Multiple failures listed clearly in summary."""
        profile = UserProfileInput(
            age=15,  # Fails min_age
            annual_income=500000.0,  # Fails max_income
            gender="MALE",  # Fails gender
        )
        scheme = {"government_level": "CENTRAL"}
        rules = {"min_age": 18, "max_income": 200000.0, "gender": "FEMALE"}
        res = evaluate_eligibility(profile, scheme, rules)
        self.assertEqual(res.status, EligibilityStatus.NOT_ELIGIBLE)
        self.assertEqual(res.failed_criteria_count, 3)


class TestEligibilityAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.routes.eligibility_routes.eligibility_service.evaluate_scheme")
    def test_post_evaluate_endpoint_success(self, mock_evaluate):
        """Verify POST /api/eligibility/evaluate returns structured response."""
        test_scheme_id = "11111111-1111-1111-1111-111111111111"
        mock_evaluate.return_value = {
            "scheme_id": test_scheme_id,
            "scheme_name": "Test PMAY Scheme",
            "government_level": "CENTRAL",
            "evaluation": {
                "status": "ELIGIBLE",
                "display_status": "🟢 Eligible",
                "summary": "All mandatory eligibility criteria are fully satisfied.",
                "criteria": [
                    {
                        "criterion": "age",
                        "result": "PASS",
                        "user_value": 25,
                        "required": ">=18",
                        "reason": "Age is valid.",
                    }
                ],
                "passed_criteria_count": 1,
                "failed_criteria_count": 0,
                "unknown_criteria_count": 0,
            },
        }

        payload = {
            "scheme_id": test_scheme_id,
            "profile": {"age": 25, "annual_income": 150000},
        }
        response = self.client.post("/api/eligibility/evaluate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["scheme_id"], test_scheme_id)
        self.assertEqual(data["evaluation"]["status"], "ELIGIBLE")
        self.assertEqual(data["evaluation"]["display_status"], "🟢 Eligible")

    @patch("app.routes.eligibility_routes.eligibility_service.evaluate_scheme")
    def test_post_evaluate_endpoint_not_found(self, mock_evaluate):
        """Verify 404 when scheme does not exist."""
        mock_evaluate.return_value = None
        payload = {
            "scheme_id": "00000000-0000-0000-0000-000000000000",
            "profile": {"age": 30},
        }
        response = self.client.post("/api/eligibility/evaluate", json=payload)
        self.assertEqual(response.status_code, 404)

    @patch("app.routes.eligibility_routes.eligibility_service.evaluate_all_schemes")
    def test_get_bulk_schemes_endpoint(self, mock_bulk):
        """Verify GET /api/eligibility/schemes returns bulk evaluation."""
        mock_bulk.return_value = {
            "total_evaluated": 2,
            "eligible_count": 1,
            "possibly_eligible_count": 1,
            "not_eligible_count": 0,
            "results": [
                {
                    "scheme_id": "11111111-1111-1111-1111-111111111111",
                    "scheme_name": "Scheme A",
                    "government_level": "CENTRAL",
                    "evaluation": {
                        "status": "ELIGIBLE",
                        "display_status": "🟢 Eligible",
                        "summary": "Passed all.",
                        "criteria": [],
                        "passed_criteria_count": 0,
                        "failed_criteria_count": 0,
                        "unknown_criteria_count": 0,
                    },
                },
                {
                    "scheme_id": "22222222-2222-2222-2222-222222222222",
                    "scheme_name": "Scheme B",
                    "government_level": "CENTRAL",
                    "evaluation": {
                        "status": "POSSIBLY_ELIGIBLE",
                        "display_status": "🟡 Possibly Eligible",
                        "summary": "Need info.",
                        "criteria": [],
                        "passed_criteria_count": 0,
                        "failed_criteria_count": 0,
                        "unknown_criteria_count": 1,
                    },
                },
            ],
        }

        response = self.client.get("/api/eligibility/schemes?age=25&annual_income=150000")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_evaluated"], 2)
        self.assertEqual(data["eligible_count"], 1)
        self.assertEqual(data["possibly_eligible_count"], 1)


class TestPhase3SecurityAndExplanationAudit(unittest.TestCase):
    """
    Focused regression and security tests for Phase 3 audit:
      1. Authenticated user profile security & isolation via auth.uid()
      2. Forbidding arbitrary profile dictionary overrides for authenticated users
      3. Forbidding cross-user profile access
      4. Forbidding guest access to private user_profiles
      5. Accurate explanations for unrestricted criteria without fabricated requirements
      6. Verifying education hierarchy determinism
    """

    def setUp(self):
        self.client = TestClient(app)
        self.engine = DeterministicEligibilityEngine()
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
        self.test_scheme_id = "33333333-3333-3333-3333-333333333333"

    # ==========================================
    # 1. AUTHENTICATED PROFILE SECURITY TESTS
    # ==========================================
    def test_authenticated_profile_cannot_be_overridden(self):
        """Authenticated user cannot supply arbitrary profile dictionary to override DB profile."""
        headers = {"Authorization": f"Bearer {self.token_user_a}"}
        payload = {
            "scheme_id": self.test_scheme_id,
            "profile": {"age": 99, "annual_income": 0},
        }
        response = self.client.post("/api/eligibility/evaluate", json=payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("cannot override their database profile", response.json()["detail"])

    def test_authenticated_user_cannot_access_another_users_profile(self):
        """Authenticated user A cannot specify user_id of user B (cross-user access blocked)."""
        headers = {"Authorization": f"Bearer {self.token_user_a}"}
        payload = {
            "scheme_id": self.test_scheme_id,
            "user_id": self.user_b_id,
        }
        response = self.client.post("/api/eligibility/evaluate", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Cross-user access denied", response.json()["detail"])

    def test_guest_request_cannot_access_private_user_profiles(self):
        """Unauthenticated guest request cannot specify user_id to query private profile."""
        payload = {
            "scheme_id": self.test_scheme_id,
            "user_id": self.user_a_id,
        }
        response = self.client.post("/api/eligibility/evaluate", json=payload)
        self.assertEqual(response.status_code, 401)
        self.assertIn("cannot access private user profiles", response.json()["detail"])

    def test_authenticated_user_uses_auth_uid(self):
        """Authenticated request without profile override uses auth.uid() from token."""
        headers = {"Authorization": f"Bearer {self.token_user_a}"}
        payload = {
            "scheme_id": self.test_scheme_id,
        }
        with patch("app.routes.eligibility_routes.eligibility_service.evaluate_scheme") as mock_eval:
            mock_eval.return_value = {
                "scheme_id": self.test_scheme_id,
                "scheme_name": "Test Scheme",
                "government_level": "CENTRAL",
                "evaluation": {
                    "status": "ELIGIBLE",
                    "display_status": "🟢 Eligible",
                    "summary": "All satisfied",
                    "criteria": [],
                    "passed_criteria_count": 0,
                    "failed_criteria_count": 0,
                    "unknown_criteria_count": 0,
                },
            }
            response = self.client.post("/api/eligibility/evaluate", json=payload, headers=headers)
            self.assertEqual(response.status_code, 200)
            mock_eval.assert_called_once_with(
                scheme_id=self.test_scheme_id,
                user_id=self.user_a_id,
                profile_input=None,
            )

    def test_bulk_schemes_cross_user_access_blocked(self):
        """GET /api/eligibility/schemes blocks user A from requesting user B's evaluations."""
        headers = {"Authorization": f"Bearer {self.token_user_a}"}
        response = self.client.get(f"/api/eligibility/schemes?user_id={self.user_b_id}", headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_bulk_schemes_authenticated_override_blocked(self):
        """GET /api/eligibility/schemes blocks authenticated user from passing profile override params."""
        headers = {"Authorization": f"Bearer {self.token_user_a}"}
        response = self.client.get("/api/eligibility/schemes?age=35", headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("cannot override their database profile", response.json()["detail"])

    def test_bulk_schemes_guest_cannot_access_user_id(self):
        """GET /api/eligibility/schemes blocks guest from passing user_id."""
        response = self.client.get(f"/api/eligibility/schemes?user_id={self.user_a_id}")
        self.assertEqual(response.status_code, 401)

    # ==========================================
    # 2. EXPLANATION ACCURACY TESTS
    # ==========================================
    def test_unrestricted_age_does_not_present_fabricated_120_bound(self):
        """Scheme without upper age limit does not fabricate '<=120' requirement."""
        # e.g., min_age=18, max_age=120 (stored placeholder)
        res = self.engine.evaluate_age(user_age=35, min_age=18, max_age=120)
        self.assertIsNotNone(res)
        self.assertEqual(res.required, ">=18")
        self.assertNotIn("120", res.required)
        self.assertNotIn("120", res.reason)

    def test_unrestricted_age_outputs_clear_explanation(self):
        """Scheme with no age restrictions outputs 'No age restriction specified'."""
        res_explicit = self.engine.evaluate_age(user_age=35, min_age=None, max_age=None, include_unrestricted=True)
        self.assertIsNotNone(res_explicit)
        self.assertEqual(res_explicit.required, "No age restriction specified")
        self.assertEqual(res_explicit.reason, "No age restriction specified for this scheme.")
        self.assertEqual(res_explicit.result, CriterionResult.PASS)

        # Placeholder min_age=0, max_age=120
        res_dummy = self.engine.evaluate_age(user_age=35, min_age=0, max_age=120)
        self.assertIsNotNone(res_dummy)
        self.assertEqual(res_dummy.required, "No age restriction specified")
        self.assertEqual(res_dummy.reason, "No age restriction specified for this scheme.")

    def test_unrestricted_criteria_produce_accurate_explanations(self):
        """Unrestricted criteria for income, gender, occupation, etc. produce accurate statements."""
        # Income
        inc_eval = self.engine.evaluate_income(user_income=150000, max_income=None, include_unrestricted=True)
        self.assertEqual(inc_eval.required, "No income restriction specified")
        self.assertEqual(inc_eval.result, CriterionResult.PASS)

        # Gender
        gen_eval = self.engine.evaluate_gender(user_gender="FEMALE", scheme_gender="ALL", include_unrestricted=True)
        self.assertEqual(gen_eval.required, "No gender restriction specified")
        self.assertEqual(gen_eval.result, CriterionResult.PASS)

        # Occupation
        occ_eval = self.engine.evaluate_occupation(user_occ="Doctor", scheme_occ=None, include_unrestricted=True)
        self.assertEqual(occ_eval.required, "No occupation restriction specified")
        self.assertEqual(occ_eval.result, CriterionResult.PASS)

        # Education
        edu_eval = self.engine.evaluate_education(user_edu="Graduate", scheme_edu=None, include_unrestricted=True)
        self.assertEqual(edu_eval.required, "No education restriction specified")
        self.assertEqual(edu_eval.result, CriterionResult.PASS)

        # Category
        cat_eval = self.engine.evaluate_category(user_cat="General", scheme_cat=None, include_unrestricted=True)
        self.assertEqual(cat_eval.required, "No category restriction specified")
        self.assertEqual(cat_eval.result, CriterionResult.PASS)

        # Disability
        dis_eval = self.engine.evaluate_disability(user_disability=False, disability_required=False, include_unrestricted=True)
        self.assertEqual(dis_eval.required, "No disability restriction specified")
        self.assertEqual(dis_eval.result, CriterionResult.PASS)

        # State (Central All India)
        state_eval = self.engine.evaluate_state(
            user_state_id=1, government_level="CENTRAL", scheme_state_id=None, state_restriction=None
        )
        self.assertEqual(state_eval.required, "No state restriction specified (All India)")
        self.assertEqual(state_eval.result, CriterionResult.PASS)

        # District
        dist_eval = self.engine.evaluate_district(user_district_id=1, district_restriction=None, include_unrestricted=True)
        self.assertEqual(dist_eval.required, "No district restriction specified")
        self.assertEqual(dist_eval.result, CriterionResult.PASS)

    def test_no_fabricated_requirement_appears_in_explanation(self):
        """Full scheme evaluation with empty rules produces no invented requirements."""
        profile = UserProfileInput(age=25, annual_income=100000)
        scheme = {"scheme_name": "Open Scheme", "government_level": "CENTRAL"}
        rules = {}
        res = evaluate_eligibility(profile, scheme, rules, include_unrestricted=True)
        for criterion in res.criteria:
            self.assertIn("No ", criterion.required)
            self.assertNotIn("120", criterion.required)
            self.assertNotIn("120", criterion.reason)

    # ==========================================
    # 3. EDUCATION HIERARCHY TESTS
    # ==========================================
    def test_education_hierarchy_deterministic(self):
        """Verify deterministic education comparisons across hierarchy tiers."""
        # Citizen tier 1 (Primary) vs Scheme tier 6 (Graduate) => FAIL
        res_fail = self.engine.evaluate_education(user_edu="Primary", scheme_edu="Graduate")
        self.assertEqual(res_fail.result, CriterionResult.FAIL)
        self.assertIn("below the required threshold", res_fail.reason)

        # Citizen tier 7 (Postgraduate) vs Scheme tier 6 (Graduate) => PASS
        res_pass = self.engine.evaluate_education(user_edu="Postgraduate", scheme_edu="Graduate")
        self.assertEqual(res_pass.result, CriterionResult.PASS)
        self.assertIn("meets or exceeds required tier", res_pass.reason)

        # Scheme without education requirement does not invent any education requirement
        res_none = self.engine.evaluate_education(user_edu="Primary", scheme_edu=None, include_unrestricted=True)
        self.assertEqual(res_none.required, "No education restriction specified")
        self.assertEqual(res_none.result, CriterionResult.PASS)


if __name__ == "__main__":
    unittest.main()
