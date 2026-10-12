"""
Unit Tests for myScheme Normalizer & Deterministic Extractor (Phase 11F)
-------------------------------------------------------------------------
Covers the 5 key correction audit requirements:
  1. no close_date (no invented dates, maps to NO_DEADLINE)
  2. third-party URL (third-party domains never assigned to official_url)
  3. document mandatory unknown (unspecified documents flagged with unknown status)
  4. special-category age exception (preserves branches without losing special terms)
  5. district/location-dependent income condition (avoids false static scalar when location-variant)
"""

import os
import sys
import pytest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.data_pipeline.importers.myscheme_normalizer import MySchemeNormalizer
from app.models.deadline import DeadlineClassification
from app.services.deadline_service import classify_deadline


@pytest.fixture
def mock_lookups():
    state_lookup = {
        "tamil nadu": (23, "Tamil Nadu"),
        "tn": (23, "Tamil Nadu"),
    }
    category_lookup = {
        "social welfare & empowerment": (10, "Social Welfare & Empowerment"),
        "business & entrepreneurship": (3, "Business & Entrepreneurship"),
        "women and child development": (14, "Women and Child Development"),
        "housing & shelter": (6, "Housing & Shelter"),
    }
    return state_lookup, category_lookup


class TestMySchemeNormalizerAudit:
    """Test suite verifying audited myScheme normalization rules."""

    def test_1_no_close_date_mapped_to_no_deadline(self, mock_lookups):
        """Verify null scheme_close_date does not invent dates and maps to NO_DEADLINE."""
        state_lookup, category_lookup = mock_lookups
        search_item = {
            "slug": "test_scheme",
            "scheme_name": "Test Scheme",
            "level": "State",
            "beneficiary_states": ["Tamil Nadu"],
        }
        detail_item = {
            "slug": "test_scheme",
            "scheme_name": "Test Scheme",
            "level": "State",
            "scheme_open_date": None,
            "scheme_close_date": None,
            "brief_description": "Test description",
            "references": [],
        }

        normalized, _, _, audit = MySchemeNormalizer.normalize_scheme(
            search_item, detail_item, state_lookup, category_lookup
        )

        assert normalized.last_date is None
        assert normalized.start_date is None
        assert audit["has_close_date"] is False

        # Verify against Phase 4 deadline classifier
        deadline_class, days, reason = classify_deadline(normalized.last_date)
        assert deadline_class == DeadlineClassification.NO_DEADLINE
        assert days is None

    def test_2_third_party_url_not_promoted_to_official(self, mock_lookups):
        """Verify third-party domains (govtschemes.in) are never promoted to official_url."""
        state_lookup, category_lookup = mock_lookups
        search_item = {
            "slug": "test_third_party",
            "scheme_name": "Third Party Test",
            "level": "State",
            "beneficiary_states": ["Tamil Nadu"],
        }
        detail_item = {
            "slug": "test_third_party",
            "scheme_name": "Third Party Test",
            "level": "State",
            "references": [
                {"title": "Blog Guide", "url": "https://govtschemes.in/sites/default/files/guidelines.pdf"},
                {"title": "Yojana Info", "url": "https://pmmodiyojana.in/application-form.pdf"},
            ],
            "application_process": [],
        }

        normalized, _, _, audit = MySchemeNormalizer.normalize_scheme(
            search_item, detail_item, state_lookup, category_lookup
        )

        # official_url must be None because no .gov.in / .nic.in domain was present
        assert normalized.official_url is None
        assert audit["has_verified_official_url"] is False
        assert audit["third_party_only"] is True
        assert len(audit["third_party_urls"]) == 2
        # source_url retains the reference URL for traceability
        assert "govtschemes.in" in normalized.source_url
        assert any("third-party domains" in w for w in audit["validation_warnings"])

        # Compare with a legitimate government URL
        detail_gov = {
            "slug": "test_gov",
            "scheme_name": "Gov Scheme Test",
            "level": "State",
            "references": [
                {"title": "Official Portal", "url": "https://www.tnsocialwelfare.tn.gov.in/en/schemes"},
            ],
        }
        norm_gov, _, _, audit_gov = MySchemeNormalizer.normalize_scheme(
            search_item, detail_gov, state_lookup, category_lookup
        )
        assert norm_gov.official_url == "https://www.tnsocialwelfare.tn.gov.in/en/schemes"
        assert audit_gov["has_verified_official_url"] is True

    def test_3_document_mandatory_unknown_handling(self):
        """Verify documents without explicit mandatory wording are marked with unknown status."""
        raw_doc_text = """
        1. Income Certificate.
        2. Proof of age (mandatory at the time of applying).
        3. Community Certificate (optional if General category).
        4. Ration Card.
        """
        parsed_docs, unknown_count, explicit_count = MySchemeNormalizer.parse_documents(raw_doc_text)

        assert len(parsed_docs) == 4
        # Income Certificate and Ration Card have unknown mandatory status
        assert unknown_count == 2
        assert explicit_count == 1  # only Proof of age is explicit mandatory

        # Check description annotations
        doc_map = {d.document_name: d for d in parsed_docs}
        assert "MANDATORY_STATUS_UNKNOWN" in doc_map["Income Certificate."].description
        assert "MANDATORY_STATUS_UNKNOWN" in doc_map["Ration Card."].description
        assert "Explicitly stated as mandatory" in doc_map["Proof of age (mandatory at the time of applying)."].description
        assert doc_map["Community Certificate (optional if General category)."].mandatory is False

    def test_4_special_category_age_exception(self):
        """Verify category-based age limits preserve the base limit and special branches."""
        eligibility_text = """
        1. The applicant should be a minimum of 18 years of age.
        2. (a) for the General category: maximum of 35 years of age.
           (b) for Special category (SC/ST/MBC/BC/Minorities/Ex-Servicemen/Transgender): maximum of 45 years of age.
        3. The family income should not exceed ₹5 lakhs per annum.
        """
        elig, unparsed, flags = MySchemeNormalizer.extract_deterministic_eligibility(eligibility_text, state_id=23)

        assert elig.min_age == 18
        assert elig.max_age == 35  # General base
        assert elig.max_income == 500000.0

        # Special category extension branch must be preserved in other_conditions
        special_branches = elig.other_conditions.get("special_branches", [])
        assert any("maximum of 45 years" in b for b in special_branches)
        assert any("Category-dependent age limit" in f for f in flags)

    def test_5_district_dependent_income_condition(self):
        """Verify location-dependent income limits do not invent a static scalar and preserve mapping."""
        eligibility_text = """
        1. The applicant should be a working woman.
        2. If the applicant is in Chennai, the income of the applicant should not exceed ₹25000/- per month.
        3. If the applicant is in a district other than Chennai, the income of the applicant should not exceed ₹15000/- per month.
        """
        elig, unparsed, flags = MySchemeNormalizer.extract_deterministic_eligibility(eligibility_text, state_id=23)

        # max_income must be None to prevent false static rejection for applicants in different districts
        assert elig.max_income is None
        assert elig.gender == "FEMALE"
        assert elig.occupation == "Working Women"

        district_incomes = elig.other_conditions.get("district_income_conditions", {})
        assert district_incomes.get("Chennai") == 300000.0  # 25,000 * 12
        assert district_incomes.get("Other_Districts") == 180000.0  # 15,000 * 12
        assert any("District-dependent income ceiling" in f for f in flags)
