"""
OpenAI Integration Service
--------------------------
Provides server-side OpenAI client integration for multi-factor relevance ranking.

ARCHITECTURAL SAFEGUARDS:
1. The OpenAI API key is read solely server-side from environment variables.
2. Data minimization: Sends only non-sensitive demographic tags and scheme metadata.
   Never sends tokens, passwords, database IDs, or sensitive family records.
3. Strict Prompt Safety: Instructs the LLM that legal eligibility is already resolved;
   the LLM is strictly prohibited from altering eligibility or hallucinating schemes.
4. Structured Output Validation: Validates response against AIRankingOutput Pydantic schema,
   clamps scores to [0, 100], and discards unknown or hallucinated scheme IDs.
5. Graceful Failure: Never raises unhandled 500s on timeouts, rate limits, or missing keys;
   returns None to trigger explainable deterministic fallback ranking.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Set

from app.models.eligibility import UserProfileInput
from app.models.recommendation import AIRankedItem, AIRankingOutput

logger = logging.getLogger(__name__)

# Default OpenAI model for recommendation ranking
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
OPENAI_REQUEST_TIMEOUT = 10.0  # seconds


class OpenAIService:
    """Server-side OpenAI integration client for structured scheme ranking."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        self._client = None

    @property
    def client(self):
        """Lazy-initialize OpenAI client if key is configured."""
        if self._client is None and self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, timeout=OPENAI_REQUEST_TIMEOUT)
            except Exception as exc:
                logger.warning("Failed to initialize OpenAI client: %s", exc)
                self._client = None
        return self._client

    def is_available(self) -> bool:
        """Check if OpenAI service is configured and client initialized."""
        return bool(self.api_key and self.api_key.strip() and self.client is not None)

    def prepare_sanitized_user_context(
        self, profile: UserProfileInput, query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Data Minimization:
        Extracts only demographic attributes pertinent to scheme relevance.
        Excludes passwords, auth tokens, database IDs, and sensitive personal data.
        """
        context: Dict[str, Any] = {}
        if profile.age is not None:
            context["age"] = profile.age
        if profile.gender:
            context["gender"] = profile.gender
        if profile.state_name:
            context["state"] = profile.state_name
        elif profile.state_id is not None:
            context["state_id"] = profile.state_id
        if profile.district_name:
            context["district"] = profile.district_name
        elif profile.district_id is not None:
            context["district_id"] = profile.district_id
        if profile.occupation:
            context["occupation"] = profile.occupation
        if profile.education:
            context["education"] = profile.education
        if profile.category:
            context["social_category"] = profile.category
        if profile.disability_status is not None:
            context["disability_status"] = profile.disability_status
        if query and query.strip():
            context["citizen_expressed_need"] = query.strip()

        return context

    def prepare_candidate_metadata(
        self, candidate_schemes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract compact metadata for candidate schemes to minimize prompt size."""
        sanitized_candidates = []
        for scheme in candidate_schemes:
            s_id = str(scheme.get("id"))
            name = scheme.get("scheme_name", "")
            cat = scheme.get("category_name") or ""
            desc = scheme.get("description") or scheme.get("brief_summary") or ""
            # Truncate description to avoid prompt bloat
            short_desc = desc[:250] + ("..." if len(desc) > 250 else "")
            benefits = scheme.get("benefits") or ""
            short_benefits = benefits[:200] + ("..." if len(benefits) > 200 else "")

            sanitized_candidates.append({
                "scheme_id": s_id,
                "scheme_name": name,
                "category": cat,
                "summary": short_desc,
                "benefits": short_benefits,
            })
        return sanitized_candidates

    def rank_schemes(
        self,
        candidate_schemes: List[Dict[str, Any]],
        profile: UserProfileInput,
        query: Optional[str] = None,
    ) -> Optional[AIRankingOutput]:
        """
        Invokes OpenAI to rank deterministically eligible schemes based on relevance.
        Returns validated AIRankingOutput or None if AI ranking fails.
        """
        if not self.is_available() or not candidate_schemes:
            return None

        valid_scheme_ids: Set[str] = {str(s["id"]) for s in candidate_schemes if "id" in s}
        user_context = self.prepare_sanitized_user_context(profile, query)
        candidate_metadata = self.prepare_candidate_metadata(candidate_schemes)

        system_prompt = (
            "You are an expert government welfare scheme relevance ranking assistant.\n\n"
            "CRITICAL ARCHITECTURAL RULES:\n"
            "1. Eligibility has ALREADY been legally determined by a deterministic legal rule engine. "
            "Every single scheme in the candidate list is 100% ELIGIBLE and OPEN for application.\n"
            "2. DO NOT evaluate or alter eligibility. Your sole job is to rank these already-eligible "
            "schemes by relevance match to the citizen's profile and stated request.\n"
            "3. Score each scheme from 0 to 100 based on fit, utility, and expressed need. "
            "A score of 100 means highly relevant match; 0 means lowest priority.\n"
            "4. Only rank schemes from the provided candidate list. Never invent or introduce external schemes.\n"
            "5. Never hallucinate scheme details, benefits, application URLs, or deadlines.\n"
            "6. Output MUST be valid JSON conforming exactly to this structure:\n"
            '{"ranked_schemes": [{"scheme_id": "string", "relevance_score": integer (0-100), "reason": "string"}]}'
        )

        user_prompt = (
            f"Citizen Profile & Request:\n{json.dumps(user_context, indent=2)}\n\n"
            f"Eligible Candidate Schemes to Rank:\n{json.dumps(candidate_metadata, indent=2)}\n\n"
            "Please rank all candidate schemes by relevance and return structured JSON."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                logger.warning("Empty response from OpenAI")
                return None

            data = json.loads(raw_content)
            raw_items = data.get("ranked_schemes", [])

            # Validate and sanitize AI output against candidate set
            validated_items: List[AIRankedItem] = []
            seen_ids: Set[str] = set()

            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                s_id = str(item.get("scheme_id", "")).strip()

                # Discard hallucinated scheme IDs not supplied in candidates
                if s_id not in valid_scheme_ids:
                    logger.warning("Discarded unknown scheme_id from AI output: %s", s_id)
                    continue

                # Deduplicate repeated scheme IDs
                if s_id in seen_ids:
                    continue
                seen_ids.add(s_id)

                # Clamp score to [0, 100]
                raw_score = item.get("relevance_score", 50)
                try:
                    score = int(raw_score)
                except (ValueError, TypeError):
                    score = 50
                clamped_score = max(0, min(score, 100))

                reason = str(item.get("reason", "Relevant to citizen profile.")).strip()
                if not reason:
                    reason = "Matches citizen profile."

                validated_items.append(
                    AIRankedItem(
                        scheme_id=s_id,
                        relevance_score=clamped_score,
                        reason=reason,
                    )
                )

            return AIRankingOutput(ranked_schemes=validated_items)

        except Exception as exc:
            logger.warning("OpenAI ranking failed, falling back to deterministic ranker: %s", exc)
            return None

    def extract_chat_intent(
        self,
        message: str,
        user_profile: Optional[UserProfileInput] = None,
    ) -> Any:
        """
        Extracts structured intent, search keywords, and explicit demographic entities from user message.
        Falls back to pure deterministic regex/keyword extraction if OpenAI is unavailable.
        """
        from app.models.chat import ChatIntent

        clean_msg = message.strip()
        if not clean_msg:
            return ChatIntent(intent="general_inquiry", query="", language="en")

        # Fast Tamil script detection
        is_tamil = any("\u0b80" <= ch <= "\u0bff" for ch in clean_msg)
        detected_lang = "ta" if is_tamil else "en"

        if not self.is_available():
            return self._deterministic_extract_intent(clean_msg, detected_lang)

        system_prompt = (
            "You are an NLP entity extraction engine for an Indian Government welfare scheme portal.\n"
            "Analyze the user's natural-language query in English or Tamil and extract structured intent.\n\n"
            "CRITICAL RULES:\n"
            "1. STRICT FACTUAL EXTRACTION: ONLY extract values EXPLICITLY STATED by the user.\n"
            "2. NEVER GUESS OR INFER missing demographic attributes. If the user does not state their age, "
            "age MUST be null. If they do not state gender, gender MUST be null. Do not default anything.\n"
            "3. State names must be normalized to official Indian states (e.g., 'Tamil Nadu', 'Karnataka', 'Maharashtra').\n"
            "4. Language: set to 'ta' if message is in Tamil script or Tamil phrases; otherwise 'en'.\n"
            "5. Return a valid JSON object matching:\n"
            "{\n"
            '  "intent": "find_schemes" | "eligibility_query" | "general_inquiry",\n'
            '  "query": "clean search keywords in English",\n'
            '  "language": "en" | "ta",\n'
            '  "age": integer or null,\n'
            '  "gender": "MALE" | "FEMALE" | "TRANSGENDER" | "OTHER" | null,\n'
            '  "state_name": string or null,\n'
            '  "district_name": string or null,\n'
            '  "annual_income": number or null,\n'
            '  "occupation": string or null,\n'
            '  "education": string or null,\n'
            '  "category": "SC" | "ST" | "OBC" | "GENERAL" | null,\n'
            '  "disability_status": boolean or null,\n'
            '  "keywords": ["list", "of", "domain", "keywords"]\n'
            "}"
        )

        user_content = f"User Message: {clean_msg}"

        try:
            parsed = self._call_llm_extraction(system_prompt, user_content)
            if not parsed or not isinstance(parsed, dict):
                return self._deterministic_extract_intent(clean_msg, detected_lang)

            return ChatIntent(
                intent=parsed.get("intent") or "find_schemes",
                query=parsed.get("query") or clean_msg,
                language=parsed.get("language") or detected_lang,
                age=parsed.get("age"),
                gender=parsed.get("gender"),
                state_name=parsed.get("state_name"),
                district_name=parsed.get("district_name"),
                annual_income=parsed.get("annual_income"),
                occupation=parsed.get("occupation"),
                education=parsed.get("education"),
                category=parsed.get("category"),
                disability_status=parsed.get("disability_status"),
                keywords=parsed.get("keywords") or [],
            )
        except Exception as exc:
            logger.warning("OpenAI intent extraction failed, falling back to deterministic: %s", exc)
            return self._deterministic_extract_intent(clean_msg, detected_lang)

    def _call_llm_extraction(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """Invokes OpenAI Chat Completion for structured entity extraction."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        raw = response.choices[0].message.content
        if not raw:
            return None
        return json.loads(raw)

    def _deterministic_extract_intent(self, message: str, language: Optional[str] = None) -> Any:
        """
        Pure deterministic fallback extraction using regex and keyword dictionaries.
        Guarantees reliable operation even if OpenAI is unconfigured or unavailable.
        """
        import re
        from app.models.chat import ChatIntent

        text = message.lower()
        if language is None:
            is_tamil = any("\u0b80" <= ch <= "\u0bff" for ch in message)
            language = "ta" if is_tamil else "en"

        extracted_age = None
        extracted_gender = None
        extracted_state = None
        extracted_occ = None
        extracted_disability = None
        keywords: List[str] = []

        # 1. Age extraction
        age_match = re.search(r"\b(?:i\s*am\s*)?(\d{1,3})\s*(?:years?\s*old|yrs?\s*old|age|வயது)\b", text)
        if not age_match:
            age_match = re.search(r"\bage\s*(?:is|:)?\s*(\d{1,3})\b", text)
        if age_match:
            try:
                a = int(age_match.group(1))
                if 0 <= a <= 130:
                    extracted_age = a
            except ValueError:
                pass

        # 2. Gender extraction
        if re.search(r"\b(woman|female|girl|mother|lady)\b", text) or "பெண்" in text or "தாய்" in text:
            extracted_gender = "female"
        elif re.search(r"\b(man|male|boy|father)\b", text) or "ஆண்" in text:
            extracted_gender = "male"
        elif re.search(r"\b(transgender|trans)\b", text) or "திருநங்கை" in text or "திருநம்பி" in text:
            extracted_gender = "transgender"

        # 3. Occupation extraction
        if re.search(r"\b(farmer|agriculture|cultivator|farming|kisan)\b", text) or "விவசாயி" in text or "விவசாயம்" in text:
            extracted_occ = "farmer"
            keywords.extend(["agriculture", "farmer", "crop"])
            if "விவசாயி" in message:
                keywords.append("விவசாயி")
        elif re.search(r"\b(student|studying|college|school|scholarship)\b", text) or "மாணவர்" in text or "படிப்பு" in text:
            extracted_occ = "student"
            keywords.extend(["education", "scholarship", "student"])
        elif re.search(r"\b(artisan|weaver|craftsman)\b", text) or "நெசவாளர்" in text:
            extracted_occ = "artisan"
            keywords.append("artisan")

        # 4. State extraction
        if re.search(r"\b(tamil\s*nadu|tamilnadu|tn)\b", text) or "தமிழ்நாடு" in text:
            extracted_state = "Tamil Nadu"
            keywords.append("tamil nadu")
        elif re.search(r"\b(kerala)\b", text) or "கேரளா" in text:
            extracted_state = "Kerala"
        elif re.search(r"\b(karnataka)\b", text) or "கர்நாடகா" in text:
            extracted_state = "Karnataka"
        elif re.search(r"\b(andhra\s*pradesh|andhra)\b", text) or "ஆந்திரா" in text:
            extracted_state = "Andhra Pradesh"
        elif re.search(r"\b(maharashtra)\b", text) or "மகாராஷ்டிரா" in text:
            extracted_state = "Maharashtra"
        elif re.search(r"\b(delhi)\b", text) or "டெல்லி" in text:
            extracted_state = "Delhi"

        # 5. Disability extraction
        if re.search(r"\b(disabled|disability|handicapped|pwd)\b", text) or "மாற்றுத்திறனாளி" in text:
            extracted_disability = True
            keywords.append("disability")

        extracted_district = None
        extracted_income = None
        extracted_edu = None
        extracted_category = None

        # 6. District extraction (Tamil Nadu)
        tn_districts = {
            "chennai": "Chennai",
            "coimbatore": "Coimbatore",
            "madurai": "Madurai",
            "salem": "Salem",
            "tiruchirappalli": "Tiruchirappalli",
            "trichy": "Tiruchirappalli",
            "thanjavur": "Thanjavur",
            "vellore": "Vellore",
            "tirunelveli": "Tirunelveli",
            "dindigul": "Dindigul",
            "erode": "Erode",
            "tiruppur": "Tiruppur",
            "kancheepuram": "Kancheepuram",
            "cuddalore": "Cuddalore",
            "dharmapuri": "Dharmapuri",
            "krishnagiri": "Krishnagiri",
            "namakkal": "Namakkal",
            "nilgiris": "The Nilgiris",
            "karur": "Karur",
            "perambalur": "Perambalur",
            "pudukkottai": "Pudukkottai",
            "ramanathapuram": "Ramanathapuram",
            "sivaganga": "Sivaganga",
            "theni": "Theni",
            "thoothukudi": "Thoothukudi",
            "tiruvallur": "Tiruvallur",
            "tiruvannamalai": "Tiruvannamalai",
            "tiruvarur": "Tiruvarur",
            "viluppuram": "Viluppuram",
            "virudhunagar": "Virudhunagar",
            "ariyalur": "Ariyalur",
            "tenkasi": "Tenkasi",
            "tirupathur": "Tirupathur",
            "ranipet": "Ranipet",
            "chengalpattu": "Chengalpattu",
            "kallakurichi": "Kallakurichi",
            "mayiladuthurai": "Mayiladuthurai",
            "சென்னை": "Chennai",
            "கோவை": "Coimbatore",
            "மதுரை": "Madurai",
            "சேலம்": "Salem",
            "திருச்சி": "Tiruchirappalli",
            "தஞ்சாவூர்": "Thanjavur",
        }
        for d_key, d_val in tn_districts.items():
            if re.search(r"\b" + re.escape(d_key) + r"\b", text) or d_key in message:
                extracted_district = d_val
                keywords.append(d_val.lower())
                break

        # 7. Income extraction
        inc_match = re.search(r"(?:income|salary|earnings?|வருமானம்)\s*(?:is|:|\s)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:[.,]\d+)?)\s*(lakhs?|lacs?|l|crores?|k)?", text)
        if not inc_match:
            inc_match = re.search(r"(?:under|below|less than|கீழ்)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:[.,]\d+)?)\s*(lakhs?|lacs?|l|crores?|k)?\s*(?:income|annual income|வருமானம்)?", text)
        if inc_match:
            try:
                num = float(inc_match.group(1).replace(",", ""))
                unit = (inc_match.group(2) or "").lower()
                if "lakh" in unit or "lac" in unit or unit == "l" or "லட்சம்" in text:
                    extracted_income = num * 100000.0
                elif "crore" in unit:
                    extracted_income = num * 10000000.0
                elif unit == "k":
                    extracted_income = num * 1000.0
                elif num < 100:
                    extracted_income = num * 100000.0
                else:
                    extracted_income = num
            except ValueError:
                pass

        # 8. Education extraction
        if re.search(r"\b(10th|sslc|tenth|10 ஆம் வகுப்பு)\b", text):
            extracted_edu = "10th"
            keywords.append("10th")
        elif re.search(r"\b(12th|hsc|higher secondary|plus two|\+2|12 ஆம் வகுப்பு)\b", text):
            extracted_edu = "Higher Secondary (12th)"
            keywords.append("higher secondary")
        elif re.search(r"\b(diploma|polytechnic)\b", text):
            extracted_edu = "Diploma"
            keywords.append("diploma")
        elif re.search(r"\b(graduate|bachelor|degree|b\.?e|b\.?tech|b\.?sc|b\.?com|b\.?a|பட்டதாரி)\b", text):
            extracted_edu = "Graduate / Bachelor's"
            keywords.append("graduate")
        elif re.search(r"\b(post graduate|master|m\.?tech|m\.?sc|m\.?com|m\.?a|phd)\b", text):
            extracted_edu = "Post Graduate / Master's"
            keywords.append("post graduate")

        # 9. Social category extraction
        if re.search(r"\b(sc|scheduled caste|ஆதிதிராவிடர்)\b", text):
            extracted_category = "SC"
            keywords.append("sc")
        elif re.search(r"\b(st|scheduled tribe|பழங்குடியினர்)\b", text):
            extracted_category = "ST"
            keywords.append("st")
        elif re.search(r"\b(mbc|most backward|மிகவும் பிற்படுத்தப்பட்டோர்)\b", text):
            extracted_category = "MBC"
            keywords.append("mbc")
        elif re.search(r"\b(obc|bc|backward class|பிற்படுத்தப்பட்டோர்)\b", text):
            extracted_category = "OBC"
            keywords.append("obc")
        elif re.search(r"\b(general|oc|முன்னேறிய வகுப்பு)\b", text):
            extracted_category = "General"

        # 10. Specific welfare scheme recognition
        if re.search(r"\b(pudhumai\s*penn|புதுமைப் பெண்)\b", text):
            keywords.extend(["pudhumai penn", "higher education"])
        if re.search(r"\b(moovalur|ramamirtham|மூவலூர்)\b", text):
            keywords.extend(["moovalur", "marriage assistance"])
        if re.search(r"\b(uyegp|unemployed youth)\b", text):
            keywords.extend(["uyegp", "employment generation"])
        if re.search(r"\b(amma two wheeler|two wheeler|இருசக்கர வாகனம்)\b", text):
            keywords.extend(["two wheeler", "working women"])
        if re.search(r"\b(girl child|girl child protection)\b", text):
            keywords.extend(["girl child", "protection"])
        if re.search(r"\b(hostel|working women hostel|விடுதி)\b", text):
            keywords.extend(["hostel", "working women"])

        # 11. Domain keywords
        if "housing" in text or "வீடு" in text:
            keywords.append("housing")
        if "loan" in text or "credit" in text or "நிதி" in text:
            keywords.append("finance")
        if "health" in text or "medical" in text or "மருத்துவம்" in text:
            keywords.append("health")

        # 12. SPR Intent classification
        intent_type = "find_schemes"
        if re.search(r"\b(document|documents|certificate|proof|சான்றிதழ்|ஆவணங்கள்)\b", text):
            intent_type = "document_inquiry"
        elif re.search(r"\b(how to apply|application process|where to apply|portal|website|எப்படி விண்ணப்பிப்பது)\b", text):
            intent_type = "procedure_inquiry"
        elif re.search(r"\b(benefit|benefits|amount|subsidy|grant|loan|நிதி உதவி|மானியம்)\b", text):
            intent_type = "benefit_inquiry"
        elif re.search(r"\b(deadline|last date|closing date|கடைசி தேதி)\b", text):
            intent_type = "deadline_inquiry"

        return ChatIntent(
            intent=intent_type,
            query=message,
            language=language,
            age=extracted_age,
            gender=extracted_gender,
            state_name=extracted_state,
            district_name=extracted_district,
            annual_income=extracted_income,
            occupation=extracted_occ,
            education=extracted_edu,
            category=extracted_category,
            disability_status=extracted_disability,
            keywords=keywords,
        )

    def generate_chat_response(
        self,
        user_message: str,
        recommendations: list,
        verification_required: Optional[list] = None,
        language: str = "en",
        user_name: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Synthesizes a helpful natural-language conversational response for the citizen.
        Grounded strictly in the returned factual recommendations using NLP Sparse Primed Representation.
        """
        verification_required = verification_required or []
        name_str = f" {user_name}" if user_name else ""
        is_tamil = language == "ta"

        # Truthful empty state when no schemes exist or match
        if not recommendations and not verification_required:
            if is_tamil:
                return (
                    f"வணக்கம்{name_str}! இணைக்கப்பட்ட தரவுத்தளத்தில் தற்போது நேரலை திட்டப் பதிவுகள் எதுவும் கிடைக்கவில்லை. "
                    "அதிகாரப்பூர்வ அரசு மூல கையகப்படுத்தல் பைப்லைன் தயாராக உள்ளது, ஆனால் நேரடி திட்ட பதிவுகள் இன்னும் பதிவேற்றப்படவில்லை. "
                    "விரைவில் மீண்டும் சரிபார்க்கவும்."
                )
            return (
                f"Hello{name_str}! I couldn't find any government scheme records in the connected database right now. "
                "The official-source acquisition pipeline is ready, but live scheme records are currently pending ingestion. "
                "Please check back soon."
            )

        def _format_deterministic_response() -> str:
            rec_count = len(recommendations)
            verif_count = len(verification_required)

            if is_tamil:
                if rec_count > 0:
                    msg = (
                        f"வணக்கம்{name_str}! தமிழ்நாடு அரசு மற்றும் மத்திய அரசின் அதிகாரப்பூர்வ விதிமுறைகளின்படி, "
                        f"உங்கள் சுயவிவரத்திற்குப் பொருந்தும் **{rec_count} தகுதியான நலத்திட்டங்களை** கண்டறிந்துள்ளேன்.\n\n"
                        "### 🏛️ முக்கிய தகுதியான திட்டங்கள்:\n\n"
                    )
                    for idx, r in enumerate(recommendations[:3], 1):
                        s_name = getattr(r, "scheme_name", "") or r.get("scheme_name", "")
                        s_score = getattr(r, "relevance_score", 0) or r.get("relevance_score", 0)
                        s_benefit = getattr(r, "benefits", "") or r.get("benefits", "")
                        s_benefit_short = s_benefit[:120] + ("..." if len(s_benefit) > 120 else "") if s_benefit else "அரசு உதவி மற்றும் நலத்திட்ட பலன்கள் வழங்கப்படுகின்றன."

                        msg += f"**{idx}. {s_name}**\n"
                        msg += f"- **பொருத்தம்:** {s_score}/100\n"
                        msg += f"- **திட்ட பயன்கள்:** {s_benefit_short}\n\n"

                    if verif_count > 0:
                        msg += f"💡 *கூடுதலாக, ஆவணச் சரிபார்ப்பிற்கு உட்பட்ட மேலும் {verif_count} திட்டங்கள் உள்ளன.*\n\n"
                else:
                    msg = (
                        f"வணக்கம்{name_str}! தமிழ்நாடு அரசு மற்றும் மத்திய அரசின் அதிகாரப்பூர்வ விதிமுறைகளின்படி, "
                        f"உங்கள் தகவல்களின் அடிப்படையில் நீங்கள் பயன்பெறக்கூடிய **{verif_count} சாத்தியமான நலத்திட்டங்கள்** கண்டறியப்பட்டுள்ளன "
                        "(இவற்றிற்கு சான்றிதழ் அல்லது தகுதிச் சான்றுகள் சரிபார்க்கப்பட வேண்டும்):\n\n"
                        "### 🏛️ சாத்தியமான நலத்திட்டங்கள்:\n\n"
                    )
                    for idx, r in enumerate(verification_required[:3], 1):
                        s_name = getattr(r, "scheme_name", "") or r.get("scheme_name", "")
                        s_score = getattr(r, "relevance_score", 0) or r.get("relevance_score", 0)
                        s_benefit = getattr(r, "benefits", "") or r.get("benefits", "")
                        s_benefit_short = s_benefit[:120] + ("..." if len(s_benefit) > 120 else "") if s_benefit else "அரசு உதவி மற்றும் நலத்திட்ட பலன்கள் வழங்கப்படுகின்றன."

                        msg += f"**{idx}. {s_name}**\n"
                        msg += f"- **பொருத்தம்:** {s_score}/100\n"
                        msg += f"- **திட்ட பயன்கள்:** {s_benefit_short}\n"
                        missing = getattr(r, "missing_criteria", []) or []
                        if missing:
                            msg += "- **சரிபார்க்க வேண்டியவை:** வருமானம், சாதிச் சான்றிதழ் அல்லது கல்வி ஆவணங்கள்.\n"
                        msg += "\n"

                msg += (
                    "📋 **அடுத்த கட்ட நடவடிக்கைகள்:**\n"
                    "- விண்ணப்பிக்க தேவையான ஆவணங்கள்: ஆதார் அட்டை, வருமானச் சான்றிதழ், சாதிச் சான்றிதழ் மற்றும் வங்கிக் கணக்கு புத்தகம்.\n"
                    "- கீழே உள்ள அட்டைகளில் **'View Details'** அல்லது **'Apply Officially'** கிளிக் செய்து அதிகாரப்பூர்வ அரசு போர்ட்டலில் விண்ணப்பிக்கலாம்."
                )
                return msg
            else:
                if rec_count > 0:
                    msg = (
                        f"Hello{name_str}! Based on deterministic statutory eligibility verification, "
                        f"I found **{rec_count} verified welfare program(s)** matching your profile:\n\n"
                        "### 🏛️ Recommended Welfare Schemes:\n\n"
                    )
                    for idx, r in enumerate(recommendations[:3], 1):
                        s_name = getattr(r, "scheme_name", "") or r.get("scheme_name", "")
                        s_score = getattr(r, "relevance_score", 0) or r.get("relevance_score", 0)
                        s_benefit = getattr(r, "benefits", "") or r.get("benefits", "")
                        s_benefit_short = s_benefit[:140] + ("..." if len(s_benefit) > 140 else "") if s_benefit else "Financial assistance and welfare benefits per government guidelines."

                        msg += f"**{idx}. {s_name}**\n"
                        msg += f"- **Match Score:** {s_score}/100\n"
                        msg += f"- **Key Benefits:** {s_benefit_short}\n\n"

                    if verif_count > 0:
                        msg += f"💡 *Additionally, there are {verif_count} potential scheme(s) requiring document verification listed below.*\n\n"
                else:
                    msg = (
                        f"Hello{name_str}! Based on deterministic statutory evaluation, "
                        f"I found **{verif_count} potential welfare program(s)** matching your criteria. "
                        "These programs require standard documentary confirmation (e.g., student enrollment or income certificate) to finalize qualification:\n\n"
                        "### 🏛️ Potential Welfare Schemes:\n\n"
                    )
                    for idx, r in enumerate(verification_required[:3], 1):
                        s_name = getattr(r, "scheme_name", "") or r.get("scheme_name", "")
                        s_score = getattr(r, "relevance_score", 0) or r.get("relevance_score", 0)
                        s_benefit = getattr(r, "benefits", "") or r.get("benefits", "")
                        s_benefit_short = s_benefit[:140] + ("..." if len(s_benefit) > 140 else "") if s_benefit else "Financial assistance and welfare benefits per government guidelines."

                        msg += f"**{idx}. {s_name}**\n"
                        msg += f"- **Match Score:** {s_score}/100\n"
                        msg += f"- **Key Benefits:** {s_benefit_short}\n"
                        missing = getattr(r, "missing_criteria", []) or []
                        if missing:
                            msg += "- **Verification Needed:** Supporting documentation (enrollment certificate, community/income proof).\n"
                        msg += "\n"

                msg += (
                    "📋 **Application Guidelines:**\n"
                    "- Ensure you have standard supporting documents ready (Aadhaar Card, Income Certificate, Community Certificate, and Bank Passbook).\n"
                    "- Click **'View Details'** or **'Apply Officially'** below to access the verified government portal (.gov.in / .nic.in). SchemeSetu never charges any fees for welfare access."
                )
                return msg

        if not self.is_available():
            return _format_deterministic_response()

        # LLM conversational grounding with factual constraints using Sparse Primed Representation
        compact_schemes = []
        for r in recommendations[:4]:
            compact_schemes.append({
                "name": getattr(r, "scheme_name", "") or r.get("scheme_name", ""),
                "benefits": getattr(r, "benefits", "") or r.get("benefits", ""),
                "relevance_score": getattr(r, "relevance_score", 0) or r.get("relevance_score", 0),
                "reason": getattr(r, "relevance_reason", "") or r.get("relevance_reason", ""),
            })

        compact_potential = []
        for r in verification_required[:4]:
            compact_potential.append({
                "name": getattr(r, "scheme_name", "") or r.get("scheme_name", ""),
                "benefits": getattr(r, "benefits", "") or r.get("benefits", ""),
                "relevance_score": getattr(r, "relevance_score", 0) or r.get("relevance_score", 0),
                "missing_criteria": getattr(r, "missing_criteria", []) or [],
            })

        system_prompt = (
            "You are SchemeSetu's AI Government Welfare Scheme Assistant — an authoritative, "
            "dignified, and empathetic civic advisor for Indian citizens.\n\n"
            "[SPR COGNITIVE PRIMES]\n"
            "- [PRIME: DETERMINISTIC_STATUTORY_AUTHORITY]: The server-side rule engine has already verified legal qualification. "
            "Explain criteria factually. Never overrule statutory decisions.\n"
            "- [PRIME: ZERO_HALLUCINATION_GROUNDING]: Strictly cite only programs in the Recommended or Potential Schemes context. Never invent programs, funding amounts, or deadlines.\n"
            "- [PRIME: CIVIC_PROFESSIONALISM]: Use respectful, clear, structured Markdown. Use bullet points for readability. Explain benefits, application steps, and required documents.\n"
            "- [PRIME: ANTI_PHISHING_GOV_ONLY]: Instruct the citizen to apply exclusively through official government domains (*.gov.in / *.nic.in).\n"
            f"- [PRIME: LINGUISTIC_PURITY]: Output strictly in {'TAMIL (தமிழ்) using dignified administrative Tamil terms' if is_tamil else 'professional, accessible ENGLISH'}.\n"
            "- [PRIME: METRIC_INTEGRITY]: Use 'Match Score: X/100'. Never describe relevance as legal eligibility percentage."
        )

        user_prompt = (
            f"Citizen Query: {user_message}\n\n"
            f"Recommended Eligible Schemes:\n{json.dumps(compact_schemes, indent=2)}\n\n"
            f"Potential Schemes (Requiring Document Verification):\n{json.dumps(compact_potential, indent=2)}\n\n"
            "Please write a helpful conversational summary response for the citizen."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=600,
            )
            ans = response.choices[0].message.content
            if ans and ans.strip():
                return ans.strip()
        except Exception as exc:
            logger.warning("OpenAI response synthesis failed: %s", exc)

        # Fallback template if completion fails
        return _format_deterministic_response()

