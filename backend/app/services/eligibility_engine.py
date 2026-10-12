"""
Deterministic Scheme Eligibility Evaluation Engine
--------------------------------------------------
Pure, stateless, deterministic rule engine for citizen eligibility assessment.

Strict Principles:
1. Zero LLM dependency: All assessments use deterministic, reproducible logic.
2. Three-state criterion evaluations: PASS, FAIL, UNKNOWN.
3. Strict overall statuses:
   - ANY mandatory FAIL           => NOT_ELIGIBLE (🔴 Not Eligible)
   - NO FAIL + >=1 UNKNOWN        => POSSIBLY_ELIGIBLE (🟡 Possibly Eligible)
   - ALL mandatory criteria PASS  => ELIGIBLE (🟢 Eligible)
4. Missing information yields UNKNOWN, never an automatic FAIL.
5. Contradicted mandatory rules yield FAIL.
6. Match percentages are NEVER used for eligibility determination.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import re

from app.models.eligibility import (
    CriterionEvaluation,
    CriterionResult,
    DISPLAY_STATUS_MAP,
    EligibilityExplanation,
    EligibilityStatus,
    UserProfileInput,
)

# Standardized Indian Education Hierarchy (0 to 8)
EDUCATION_HIERARCHY: Dict[str, int] = {
    # Level 0: None / Illiterate
    "none": 0,
    "illiterate": 0,
    "no formal education": 0,
    # Level 1: Primary (1st - 5th)
    "primary": 1,
    "primary education": 1,
    "5th pass": 1,
    "class 5": 1,
    # Level 2: Middle / Upper Primary (6th - 8th)
    "middle": 2,
    "upper primary": 2,
    "8th pass": 2,
    "class 8": 2,
    # Level 3: Secondary / High School (9th - 10th)
    "secondary": 3,
    "10th": 3,
    "10th pass": 3,
    "matric": 3,
    "matriculation": 3,
    "sslc": 3,
    "high school": 3,
    "class 10": 3,
    # Level 4: Higher Secondary / Intermediate (11th - 12th)
    "higher secondary": 4,
    "12th": 4,
    "12th pass": 4,
    "intermediate": 4,
    "plus two": 4,
    "+2": 4,
    "hsc": 4,
    "class 12": 4,
    # Level 5: Diploma / Vocational / ITI
    "diploma": 5,
    "polytechnic": 5,
    "iti": 5,
    "vocational": 5,
    # Level 6: Graduate / Bachelor's
    "graduate": 6,
    "graduation": 6,
    "bachelor": 6,
    "bachelors": 6,
    "undergraduate": 6,
    "ug": 6,
    "b.a": 6,
    "ba": 6,
    "b.sc": 6,
    "bsc": 6,
    "b.com": 6,
    "bcom": 6,
    "b.tech": 6,
    "btech": 6,
    "b.e": 6,
    "be": 6,
    # Level 7: Postgraduate / Master's
    "postgraduate": 7,
    "post graduate": 7,
    "post graduation": 7,
    "master": 7,
    "masters": 7,
    "pg": 7,
    "m.a": 7,
    "ma": 7,
    "m.sc": 7,
    "msc": 7,
    "m.com": 7,
    "mcom": 7,
    "m.tech": 7,
    "mtech": 7,
    "mba": 7,
    # Level 8: Doctorate / M.Phil / PhD
    "doctorate": 8,
    "phd": 8,
    "ph.d": 8,
    "m.phil": 8,
    "mphil": 8,
}

CATEGORY_ALIASES: Dict[str, str] = {
    "sc": "SC",
    "scheduled caste": "SC",
    "scheduled castes": "SC",
    "st": "ST",
    "scheduled tribe": "ST",
    "scheduled tribes": "ST",
    "obc": "OBC",
    "other backward class": "OBC",
    "other backward classes": "OBC",
    "ews": "EWS",
    "economically weaker section": "EWS",
    "economically weaker sections": "EWS",
    "general": "GENERAL",
    "gen": "GENERAL",
    "open": "GENERAL",
    "ur": "GENERAL",
    "unreserved": "GENERAL",
    "mbc": "MBC",
    "most backward class": "MBC",
}


def normalize_token(text: Optional[str]) -> str:
    """Strip whitespace, collapse internal spaces, and lower case."""
    if not text:
        return ""
    return re.sub(r"[ \t]+", " ", str(text)).strip().lower()


def normalize_category_name(cat: Optional[str]) -> str:
    token = normalize_token(cat)
    return CATEGORY_ALIASES.get(token, token.upper())


class DeterministicEligibilityEngine:
    """
    Evaluates a user profile against structured scheme eligibility criteria.
    """

    @classmethod
    def evaluate_age(
        cls,
        user_age: Optional[int],
        min_age: Optional[int],
        max_age: Optional[int],
        include_unrestricted: bool = False,
    ) -> Optional[CriterionEvaluation]:
        """
        Evaluate age against min and max thresholds.
        Does NOT present dummy upper bounds (such as <=120) as government requirements.
        If unrestricted, represents clearly as 'No age restriction specified'.
        """
        has_real_min = min_age is not None and min_age > 0
        has_real_max = max_age is not None and max_age < 100

        if not has_real_min and not has_real_max:
            # If both bounds were omitted, or dummy bounds were provided (e.g. min_age=0, max_age=120)
            if include_unrestricted or (min_age is not None or max_age is not None):
                return CriterionEvaluation(
                    criterion="age",
                    result=CriterionResult.PASS,
                    user_value=user_age,
                    required="No age restriction specified",
                    reason="No age restriction specified for this scheme.",
                )
            return None

        req_parts = []
        if has_real_min:
            req_parts.append(f">={min_age}")
        if has_real_max:
            req_parts.append(f"<={max_age}")
        req_str = " and ".join(req_parts)

        if user_age is None:
            return CriterionEvaluation(
                criterion="age",
                result=CriterionResult.UNKNOWN,
                user_value=None,
                required=req_str,
                reason=f"Citizen age is unknown; scheme requires age {req_str}.",
            )

        if has_real_min and user_age < min_age:
            return CriterionEvaluation(
                criterion="age",
                result=CriterionResult.FAIL,
                user_value=user_age,
                required=req_str,
                reason=f"Citizen age ({user_age}) is below the minimum required age of {min_age}.",
            )

        if has_real_max and user_age > max_age:
            return CriterionEvaluation(
                criterion="age",
                result=CriterionResult.FAIL,
                user_value=user_age,
                required=req_str,
                reason=f"Citizen age ({user_age}) exceeds the maximum permitted age of {max_age}.",
            )

        return CriterionEvaluation(
            criterion="age",
            result=CriterionResult.PASS,
            user_value=user_age,
            required=req_str,
            reason=f"Citizen age ({user_age}) satisfies the age requirement ({req_str}).",
        )

    @classmethod
    def evaluate_income(
        cls,
        user_income: Optional[float],
        max_income: Optional[float],
        include_unrestricted: bool = False,
    ) -> Optional[CriterionEvaluation]:
        """Evaluate family annual income against maximum threshold."""
        if max_income is None or max_income <= 0:
            if include_unrestricted:
                return CriterionEvaluation(
                    criterion="annual_income",
                    result=CriterionResult.PASS,
                    user_value=f"₹{user_income:,.2f}" if user_income is not None else None,
                    required="No income restriction specified",
                    reason="No income restriction specified for this scheme.",
                )
            return None

        req_str = f"<= ₹{max_income:,.2f}"

        if user_income is None:
            return CriterionEvaluation(
                criterion="annual_income",
                result=CriterionResult.UNKNOWN,
                user_value=None,
                required=req_str,
                reason=f"Citizen annual income is unknown; scheme requires income {req_str}.",
            )

        if user_income > max_income:
            return CriterionEvaluation(
                criterion="annual_income",
                result=CriterionResult.FAIL,
                user_value=f"₹{user_income:,.2f}",
                required=req_str,
                reason=f"Citizen annual income (₹{user_income:,.2f}) exceeds the maximum ceiling of ₹{max_income:,.2f}.",
            )

        return CriterionEvaluation(
            criterion="annual_income",
            result=CriterionResult.PASS,
            user_value=f"₹{user_income:,.2f}",
            required=req_str,
            reason=f"Citizen annual income (₹{user_income:,.2f}) is within the permitted limit ({req_str}).",
        )

    @classmethod
    def evaluate_gender(
        cls,
        user_gender: Optional[str],
        scheme_gender: Optional[str],
        include_unrestricted: bool = False,
    ) -> Optional[CriterionEvaluation]:
        """Evaluate gender restrictions."""
        if not scheme_gender or scheme_gender.upper() in ("ALL", "ANY", ""):
            if include_unrestricted:
                return CriterionEvaluation(
                    criterion="gender",
                    result=CriterionResult.PASS,
                    user_value=user_gender.strip().upper() if user_gender else None,
                    required="No gender restriction specified",
                    reason="No gender restriction specified for this scheme; open to all genders.",
                )
            return None

        req_gender = scheme_gender.strip().upper()

        if not user_gender:
            return CriterionEvaluation(
                criterion="gender",
                result=CriterionResult.UNKNOWN,
                user_value=None,
                required=req_gender,
                reason=f"Citizen gender is unspecified; scheme is restricted to {req_gender}.",
            )

        u_gender = user_gender.strip().upper()
        if u_gender == req_gender:
            return CriterionEvaluation(
                criterion="gender",
                result=CriterionResult.PASS,
                user_value=u_gender,
                required=req_gender,
                reason=f"Citizen gender ({u_gender}) matches required gender ({req_gender}).",
            )

        return CriterionEvaluation(
            criterion="gender",
            result=CriterionResult.FAIL,
            user_value=u_gender,
            required=req_gender,
            reason=f"Citizen gender ({u_gender}) does not match the required gender restriction ({req_gender}).",
        )

    @classmethod
    def evaluate_occupation(
        cls,
        user_occ: Optional[str],
        scheme_occ: Optional[str],
        include_unrestricted: bool = False,
    ) -> Optional[CriterionEvaluation]:
        """Evaluate occupation constraints."""
        if not scheme_occ or scheme_occ.upper() in ("ALL", "ANY", ""):
            if include_unrestricted:
                return CriterionEvaluation(
                    criterion="occupation",
                    result=CriterionResult.PASS,
                    user_value=user_occ.strip() if user_occ else None,
                    required="No occupation restriction specified",
                    reason="No occupation restriction specified for this scheme; open to all occupations.",
                )
            return None

        req_occ = scheme_occ.strip()

        if not user_occ:
            return CriterionEvaluation(
                criterion="occupation",
                result=CriterionResult.UNKNOWN,
                user_value=None,
                required=req_occ,
                reason=f"Citizen occupation is unspecified; scheme requires: '{req_occ}'.",
            )

        u_occ_norm = normalize_token(user_occ)
        # Parse potential comma/slash separated target occupations
        req_targets = [normalize_token(t) for t in re.split(r"[,/|]", req_occ) if t.strip()]

        # Exact match or word boundary containment
        match = any(
            t == u_occ_norm or t in u_occ_norm or u_occ_norm in t
            for t in req_targets
        )

        if match:
            return CriterionEvaluation(
                criterion="occupation",
                result=CriterionResult.PASS,
                user_value=user_occ.strip(),
                required=req_occ,
                reason=f"Citizen occupation ('{user_occ.strip()}') matches required occupation '{req_occ}'.",
            )

        return CriterionEvaluation(
            criterion="occupation",
            result=CriterionResult.FAIL,
            user_value=user_occ.strip(),
            required=req_occ,
            reason=f"Citizen occupation ('{user_occ.strip()}') does not match required occupation '{req_occ}'.",
        )

    @classmethod
    def evaluate_education(
        cls,
        user_edu: Optional[str],
        scheme_edu: Optional[str],
        include_unrestricted: bool = False,
    ) -> Optional[CriterionEvaluation]:
        """Evaluate educational attainment using the formal hierarchy."""
        if not scheme_edu or scheme_edu.upper() in ("ALL", "ANY", "NONE", ""):
            if include_unrestricted:
                return CriterionEvaluation(
                    criterion="education",
                    result=CriterionResult.PASS,
                    user_value=user_edu.strip() if user_edu else None,
                    required="No education restriction specified",
                    reason="No education restriction specified for this scheme; no minimum education required.",
                )
            return None

        req_edu = scheme_edu.strip()

        if not user_edu:
            return CriterionEvaluation(
                criterion="education",
                result=CriterionResult.UNKNOWN,
                user_value=None,
                required=f">= {req_edu}",
                reason=f"Citizen educational qualification is unspecified; scheme requires >= '{req_edu}'.",
            )

        u_norm = normalize_token(user_edu)
        s_norm = normalize_token(scheme_edu)

        u_level = EDUCATION_HIERARCHY.get(u_norm)
        s_level = EDUCATION_HIERARCHY.get(s_norm)

        # Hierarchical comparison if both keys are known
        if u_level is not None and s_level is not None:
            if u_level >= s_level:
                return CriterionEvaluation(
                    criterion="education",
                    result=CriterionResult.PASS,
                    user_value=user_edu.strip(),
                    required=f">= {req_edu}",
                    reason=f"Citizen education level '{user_edu.strip()}' (tier {u_level}) meets or exceeds required tier '{req_edu}' (tier {s_level}).",
                )
            else:
                return CriterionEvaluation(
                    criterion="education",
                    result=CriterionResult.FAIL,
                    user_value=user_edu.strip(),
                    required=f">= {req_edu}",
                    reason=f"Citizen education level '{user_edu.strip()}' (tier {u_level}) is below the required threshold of '{req_edu}' (tier {s_level}).",
                )

        # Fallback literal comparison if outside hierarchy
        if u_norm == s_norm or s_norm in u_norm:
            return CriterionEvaluation(
                criterion="education",
                result=CriterionResult.PASS,
                user_value=user_edu.strip(),
                required=req_edu,
                reason=f"Citizen education '{user_edu.strip()}' matches '{req_edu}'.",
            )

        return CriterionEvaluation(
            criterion="education",
            result=CriterionResult.FAIL,
            user_value=user_edu.strip(),
            required=f">= {req_edu}",
            reason=f"Citizen education '{user_edu.strip()}' does not meet required specification '{req_edu}'.",
        )

    @classmethod
    def evaluate_category(
        cls,
        user_cat: Optional[str],
        scheme_cat: Optional[str],
        include_unrestricted: bool = False,
    ) -> Optional[CriterionEvaluation]:
        """Evaluate social category/reservation eligibility."""
        if not scheme_cat or scheme_cat.upper() in ("ALL", "ANY", ""):
            if include_unrestricted:
                return CriterionEvaluation(
                    criterion="category",
                    result=CriterionResult.PASS,
                    user_value=user_cat.strip() if user_cat else None,
                    required="No category restriction specified",
                    reason="No category restriction specified for this scheme; open to all social categories.",
                )
            return None

        req_cat = scheme_cat.strip()

        if not user_cat:
            return CriterionEvaluation(
                criterion="category",
                result=CriterionResult.UNKNOWN,
                user_value=None,
                required=req_cat,
                reason=f"Citizen social category is unspecified; scheme is restricted to '{req_cat}'.",
            )

        u_cat_norm = normalize_category_name(user_cat)
        # Handle comma/slash separated eligible categories (e.g. "SC, ST" or "OBC, SC, ST")
        allowed_cats = {
            normalize_category_name(t)
            for t in re.split(r"[,/|]", req_cat)
            if t.strip()
        }

        if u_cat_norm in allowed_cats or "ALL" in allowed_cats:
            return CriterionEvaluation(
                criterion="category",
                result=CriterionResult.PASS,
                user_value=user_cat.strip(),
                required=req_cat,
                reason=f"Citizen category ('{user_cat.strip()}') is among eligible categories ('{req_cat}').",
            )

        return CriterionEvaluation(
            criterion="category",
            result=CriterionResult.FAIL,
            user_value=user_cat.strip(),
            required=req_cat,
            reason=f"Citizen category ('{user_cat.strip()}') does not match eligible categories ('{req_cat}').",
        )

    @classmethod
    def evaluate_disability(
        cls,
        user_disability: Optional[bool],
        disability_required: bool,
        include_unrestricted: bool = False,
    ) -> Optional[CriterionEvaluation]:
        """Evaluate disability criteria."""
        if not disability_required:
            if include_unrestricted:
                return CriterionEvaluation(
                    criterion="disability_required",
                    result=CriterionResult.PASS,
                    user_value=user_disability,
                    required="No disability restriction specified",
                    reason="No disability restriction specified for this scheme.",
                )
            return None

        req_str = "Disability status mandatory (TRUE)"

        if user_disability is None:
            return CriterionEvaluation(
                criterion="disability_required",
                result=CriterionResult.UNKNOWN,
                user_value=None,
                required=req_str,
                reason="Citizen disability status is unspecified; scheme is exclusively for persons with disabilities.",
            )

        if user_disability is True:
            return CriterionEvaluation(
                criterion="disability_required",
                result=CriterionResult.PASS,
                user_value=True,
                required=req_str,
                reason="Citizen has verified disability status as required by this scheme.",
            )

        return CriterionEvaluation(
            criterion="disability_required",
            result=CriterionResult.FAIL,
            user_value=False,
            required=req_str,
            reason="Scheme is exclusively for persons with disabilities; citizen profile indicates no disability.",
        )

    @classmethod
    def evaluate_state(
        cls,
        user_state_id: Optional[int],
        government_level: str,
        scheme_state_id: Optional[int],
        state_restriction: Optional[int],
        include_unrestricted: bool = False,
    ) -> Optional[CriterionEvaluation]:
        """
        Evaluate geographic State/UT eligibility.
        - Central schemes: applicable across India unless state_restriction is present.
        - State schemes: user state must match scheme state.
        """
        is_central = (government_level or "CENTRAL").upper() == "CENTRAL"
        target_state_id = state_restriction if state_restriction is not None else scheme_state_id

        if is_central and target_state_id is None:
            return CriterionEvaluation(
                criterion="state",
                result=CriterionResult.PASS,
                user_value=f"State ID {user_state_id}" if user_state_id else "All India",
                required="No state restriction specified (All India)",
                reason="Pan-India Central Government scheme applicable across all States and Union Territories; no state restriction specified.",
            )

        # Scheme is either STATE-level or has state_restriction
        req_str = f"State ID {target_state_id}"

        if user_state_id is None:
            return CriterionEvaluation(
                criterion="state",
                result=CriterionResult.UNKNOWN,
                user_value=None,
                required=req_str,
                reason=f"Citizen state of residence is unspecified; scheme is restricted to {req_str}.",
            )

        if user_state_id == target_state_id:
            return CriterionEvaluation(
                criterion="state",
                result=CriterionResult.PASS,
                user_value=f"State ID {user_state_id}",
                required=req_str,
                reason=f"Citizen state of residence matches the required State/UT ({req_str}).",
            )

        return CriterionEvaluation(
            criterion="state",
            result=CriterionResult.FAIL,
            user_value=f"State ID {user_state_id}",
            required=req_str,
            reason=f"Citizen resides in State ID {user_state_id}, which does not match required {req_str}.",
        )

    @classmethod
    def evaluate_district(
        cls,
        user_district_id: Optional[int],
        district_restriction: Optional[int],
        include_unrestricted: bool = False,
    ) -> Optional[CriterionEvaluation]:
        """Evaluate district-level restriction if specified."""
        if district_restriction is None:
            if include_unrestricted:
                return CriterionEvaluation(
                    criterion="district",
                    result=CriterionResult.PASS,
                    user_value=f"District ID {user_district_id}" if user_district_id else None,
                    required="No district restriction specified",
                    reason="No district restriction specified for this scheme.",
                )
            return None

        req_str = f"District ID {district_restriction}"

        if user_district_id is None:
            return CriterionEvaluation(
                criterion="district",
                result=CriterionResult.UNKNOWN,
                user_value=None,
                required=req_str,
                reason=f"Citizen district is unspecified; scheme is restricted to {req_str}.",
            )

        if user_district_id == district_restriction:
            return CriterionEvaluation(
                criterion="district",
                result=CriterionResult.PASS,
                user_value=f"District ID {user_district_id}",
                required=req_str,
                reason=f"Citizen district matches the required district ({req_str}).",
            )

        return CriterionEvaluation(
            criterion="district",
            result=CriterionResult.FAIL,
            user_value=f"District ID {user_district_id}",
            required=req_str,
            reason=f"Citizen district (ID {user_district_id}) does not match the restricted {req_str}.",
        )

    @classmethod
    def explain_unrestricted_criterion(
        cls,
        criterion: str,
        user_value: Optional[Any] = None,
    ) -> CriterionEvaluation:
        """
        Produce a standardized explanation for a criterion that has no statutory restriction.
        Never fabricates requirements or placeholder bounds.
        """
        crit = criterion.strip().lower()
        descriptions = {
            "age": ("No age restriction specified", "No age restriction specified for this scheme."),
            "annual_income": ("No income restriction specified", "No income restriction specified for this scheme."),
            "income": ("No income restriction specified", "No income restriction specified for this scheme."),
            "gender": ("No gender restriction specified", "No gender restriction specified for this scheme; open to all genders."),
            "occupation": ("No occupation restriction specified", "No occupation restriction specified for this scheme; open to all occupations."),
            "education": ("No education restriction specified", "No education restriction specified for this scheme; no minimum education required."),
            "category": ("No category restriction specified", "No category restriction specified for this scheme; open to all social categories."),
            "disability_required": ("No disability restriction specified", "No disability restriction specified for this scheme."),
            "disability": ("No disability restriction specified", "No disability restriction specified for this scheme."),
            "state": ("No state restriction specified (All India)", "Pan-India Central Government scheme applicable across all States and Union Territories; no state restriction specified."),
            "district": ("No district restriction specified", "No district restriction specified for this scheme."),
        }
        req, reason = descriptions.get(
            crit,
            (f"No {crit} restriction specified", f"No {crit} restriction specified for this scheme.")
        )
        return CriterionEvaluation(
            criterion=criterion,
            result=CriterionResult.PASS,
            user_value=user_value,
            required=req,
            reason=reason,
        )

    @classmethod
    def evaluate_other_conditions(
        cls,
        family_details: Optional[Dict[str, Any]],
        other_conditions: Optional[Dict[str, Any]],
    ) -> List[CriterionEvaluation]:
        """
        Evaluate structured JSONB other_conditions.
        Supported structured keys:
          - marital_status
          - bpl_card (bool)
          - max_landholding_hectares (float)
        Unparsed raw conditions produce a clean UNKNOWN requiring departmental verification.
        Internal pipeline metadata (flags, special_branches, district_income_conditions) is safely ignored.
        Unsupported / unmodeled structured conditions produce UNKNOWN.
        """
        evaluations: List[CriterionEvaluation] = []
        if not other_conditions or not isinstance(other_conditions, dict):
            return evaluations

        f_details = family_details or {}

        for cond_key, cond_val in other_conditions.items():
            # Skip empty / null condition values
            if cond_val is None or cond_val == "" or cond_val == [] or cond_val == {}:
                continue

            k_norm = cond_key.strip().lower()

            # Skip internal metadata keys produced by pipeline/normalizer
            if k_norm in ("flags", "verification_flags", "special_branches", "district_income_conditions"):
                continue

            # Unparsed natural language conditions from importer
            if k_norm == "raw_conditions":
                if isinstance(cond_val, list):
                    unparsed_items = [
                        str(c).strip()
                        for c in cond_val
                        if c
                        and str(c).strip()
                        and str(c).strip().lower() not in ("<br>", "<br/>", "<br />", "<p>", "</p>")
                    ]
                elif (
                    isinstance(cond_val, str)
                    and cond_val.strip()
                    and cond_val.strip().lower() not in ("<br>", "<br/>", "<br />", "<p>", "</p>")
                ):
                    unparsed_items = [cond_val.strip()]
                else:
                    unparsed_items = []

                if not unparsed_items:
                    continue

                req_summary = "; ".join(unparsed_items[:3])
                if len(unparsed_items) > 3:
                    req_summary += f" (+{len(unparsed_items) - 3} more)"

                evaluations.append(
                    CriterionEvaluation(
                        criterion="other_conditions.additional_requirements",
                        result=CriterionResult.UNKNOWN,
                        user_value=None,
                        required=req_summary,
                        reason=f"Scheme specifies additional requirements requiring verification: {'; '.join(unparsed_items)}",
                    )
                )
                continue

            # 1. Marital status condition
            if k_norm == "marital_status":
                user_val = f_details.get("marital_status")
                req_val = str(cond_val).strip().upper()
                if not user_val:
                    evaluations.append(
                        CriterionEvaluation(
                            criterion=f"other_conditions.{cond_key}",
                            result=CriterionResult.UNKNOWN,
                            user_value=None,
                            required=req_val,
                            reason=f"Marital status is unspecified; scheme requires: {req_val}.",
                        )
                    )
                elif str(user_val).strip().upper() == req_val:
                    evaluations.append(
                        CriterionEvaluation(
                            criterion=f"other_conditions.{cond_key}",
                            result=CriterionResult.PASS,
                            user_value=str(user_val).strip().upper(),
                            required=req_val,
                            reason=f"Citizen marital status '{user_val}' satisfies requirement.",
                        )
                    )
                else:
                    evaluations.append(
                        CriterionEvaluation(
                            criterion=f"other_conditions.{cond_key}",
                            result=CriterionResult.FAIL,
                            user_value=str(user_val).strip().upper(),
                            required=req_val,
                            reason=f"Citizen marital status '{user_val}' does not match required '{req_val}'.",
                        )
                    )

            # 2. BPL Card condition
            elif k_norm in ("bpl_card", "is_bpl"):
                user_val = f_details.get("bpl_card")
                req_bool = bool(cond_val)
                if user_val is None:
                    evaluations.append(
                        CriterionEvaluation(
                            criterion=f"other_conditions.{cond_key}",
                            result=CriterionResult.UNKNOWN,
                            user_value=None,
                            required="BPL cardholder",
                            reason="BPL cardholder status is unspecified.",
                        )
                    )
                elif bool(user_val) == req_bool:
                    evaluations.append(
                        CriterionEvaluation(
                            criterion=f"other_conditions.{cond_key}",
                            result=CriterionResult.PASS,
                            user_value=bool(user_val),
                            required="BPL cardholder",
                            reason="Citizen satisfies BPL requirement.",
                        )
                    )
                else:
                    evaluations.append(
                        CriterionEvaluation(
                            criterion=f"other_conditions.{cond_key}",
                            result=CriterionResult.FAIL,
                            user_value=bool(user_val),
                            required="BPL cardholder",
                            reason="Scheme requires BPL cardholder status.",
                        )
                    )

            # 3. Maximum landholding condition
            elif k_norm in ("max_landholding_hectares", "max_land_hectares"):
                user_val = f_details.get("landholding_hectares")
                try:
                    req_max = float(cond_val)
                    if user_val is None:
                        evaluations.append(
                            CriterionEvaluation(
                                criterion=f"other_conditions.{cond_key}",
                                result=CriterionResult.UNKNOWN,
                                user_value=None,
                                required=f"<= {req_max} hectares",
                                reason="Landholding size is unspecified.",
                            )
                        )
                    elif float(user_val) <= req_max:
                        evaluations.append(
                            CriterionEvaluation(
                                criterion=f"other_conditions.{cond_key}",
                                result=CriterionResult.PASS,
                                user_value=f"{float(user_val)} hectares",
                                required=f"<= {req_max} hectares",
                                reason=f"Landholding ({user_val} ha) is within permitted limit ({req_max} ha).",
                            )
                        )
                    else:
                        evaluations.append(
                            CriterionEvaluation(
                                criterion=f"other_conditions.{cond_key}",
                                result=CriterionResult.FAIL,
                                user_value=f"{float(user_val)} hectares",
                                required=f"<= {req_max} hectares",
                                reason=f"Landholding ({user_val} ha) exceeds maximum ceiling of {req_max} hectares.",
                            )
                        )
                except (ValueError, TypeError):
                    evaluations.append(
                        CriterionEvaluation(
                            criterion=f"other_conditions.{cond_key}",
                            result=CriterionResult.UNKNOWN,
                            user_value=user_val,
                            required=str(cond_val),
                            reason=f"Condition '{cond_key}' contains non-numeric threshold.",
                        )
                    )

            # 4. Unknown / Unsupported condition structure
            else:
                evaluations.append(
                    CriterionEvaluation(
                        criterion=f"other_conditions.{cond_key}",
                        result=CriterionResult.UNKNOWN,
                        user_value=f_details.get(cond_key),
                        required=str(cond_val),
                        reason=f"Condition '{cond_key}' has an unsupported or unmodeled structure and requires manual verification.",
                    )
                )

        return evaluations

    @classmethod
    def evaluate(
        cls,
        profile: UserProfileInput,
        scheme: Dict[str, Any],
        eligibility_rules: Optional[Dict[str, Any]] = None,
        include_unrestricted: bool = False,
    ) -> EligibilityExplanation:
        """
        Execute full deterministic eligibility evaluation.

        Parameters:
          profile: UserProfileInput containing citizen data
          scheme: Dict representing row from `schemes` table
          eligibility_rules: Dict representing row from `scheme_eligibility` table
          include_unrestricted: Whether to populate explicit criteria for unrestricted dimensions
        """
        rules = eligibility_rules or {}
        criteria: List[CriterionEvaluation] = []

        # 1. Age
        age_eval = cls.evaluate_age(
            profile.age,
            rules.get("min_age"),
            rules.get("max_age"),
            include_unrestricted=include_unrestricted,
        )
        if age_eval:
            criteria.append(age_eval)

        # 2. Income
        income_eval = cls.evaluate_income(
            profile.annual_income,
            rules.get("max_income"),
            include_unrestricted=include_unrestricted,
        )
        if income_eval:
            criteria.append(income_eval)

        # 3. Gender
        gender_eval = cls.evaluate_gender(
            profile.gender,
            rules.get("gender"),
            include_unrestricted=include_unrestricted,
        )
        if gender_eval:
            criteria.append(gender_eval)

        # 4. Occupation
        occ_eval = cls.evaluate_occupation(
            profile.occupation,
            rules.get("occupation"),
            include_unrestricted=include_unrestricted,
        )
        if occ_eval:
            criteria.append(occ_eval)

        # 5. Education
        edu_eval = cls.evaluate_education(
            profile.education,
            rules.get("education"),
            include_unrestricted=include_unrestricted,
        )
        if edu_eval:
            criteria.append(edu_eval)

        # 6. Category
        cat_eval = cls.evaluate_category(
            profile.category,
            rules.get("category"),
            include_unrestricted=include_unrestricted,
        )
        if cat_eval:
            criteria.append(cat_eval)

        # 7. Disability
        dis_eval = cls.evaluate_disability(
            profile.disability_status,
            bool(rules.get("disability_required", False)),
            include_unrestricted=include_unrestricted,
        )
        if dis_eval:
            criteria.append(dis_eval)

        # 8. State / Geographic
        state_eval = cls.evaluate_state(
            profile.state_id,
            scheme.get("government_level", "CENTRAL"),
            scheme.get("state_id"),
            rules.get("state_restriction"),
            include_unrestricted=include_unrestricted,
        )
        if state_eval:
            criteria.append(state_eval)

        # 9. District
        dist_eval = cls.evaluate_district(
            profile.district_id,
            rules.get("district_restriction"),
            include_unrestricted=include_unrestricted,
        )
        if dist_eval:
            criteria.append(dist_eval)

        # 10. Other Conditions
        other_evals = cls.evaluate_other_conditions(
            profile.family_details,
            rules.get("other_conditions"),
        )
        criteria.extend(other_evals)

        # Aggregation
        passed = [c for c in criteria if c.result == CriterionResult.PASS]
        failed = [c for c in criteria if c.result == CriterionResult.FAIL]
        unknown = [c for c in criteria if c.result == CriterionResult.UNKNOWN]

        # Determine overall status using 3-state logic:
        # 1. ANY mandatory FAIL => NOT_ELIGIBLE
        # 2. NO FAIL + >=1 UNKNOWN => POSSIBLY_ELIGIBLE
        # 3. ALL PASS => ELIGIBLE
        if len(failed) > 0:
            status = EligibilityStatus.NOT_ELIGIBLE
            failed_criteria_names = ", ".join([f"'{c.criterion}'" for c in failed])
            summary = (
                f"Citizen is NOT ELIGIBLE. {len(failed)} mandatory eligibility "
                f"criteria failed: {failed_criteria_names}."
            )
        elif len(unknown) > 0:
            status = EligibilityStatus.POSSIBLY_ELIGIBLE
            unknown_criteria_names = ", ".join([f"'{c.criterion}'" for c in unknown])
            summary = (
                f"Citizen is POSSIBLY ELIGIBLE. All evaluated criteria passed, "
                f"but {len(unknown)} criteria require additional profile information: {unknown_criteria_names}."
            )
        else:
            status = EligibilityStatus.ELIGIBLE
            summary = "All mandatory eligibility criteria are fully satisfied."

        return EligibilityExplanation(
            status=status,
            display_status=DISPLAY_STATUS_MAP[status],
            summary=summary,
            criteria=criteria,
            passed_criteria_count=len(passed),
            failed_criteria_count=len(failed),
            unknown_criteria_count=len(unknown),
        )


def evaluate_eligibility(
    profile: UserProfileInput,
    scheme: Dict[str, Any],
    eligibility_rules: Optional[Dict[str, Any]] = None,
    include_unrestricted: bool = False,
) -> EligibilityExplanation:
    """Convenience functional interface for scheme eligibility assessment."""
    return DeterministicEligibilityEngine.evaluate(
        profile=profile,
        scheme=scheme,
        eligibility_rules=eligibility_rules,
        include_unrestricted=include_unrestricted,
    )
