# Mini-Project Demonstration Speaking Script

**Project Title:** AI-Powered Government Scheme Recommendation System  
**Estimated Duration:** 5 to 7 Minutes  
**Audience:** College Mini-Project Review Committee / Department Evaluators  
**Tone:** Confident, Factual, Clear, Professional  

---

### [0:00 – 0:45] 1. Opening & Project Introduction
> *"Good morning, respected evaluators and faculty members. Welcome to our mini-project review.*
> 
> *Our project is the **AI-Powered Government Scheme Recommendation System**.*
> 
> *Every year, the Central and State Governments announce hundreds of welfare schemes for students, farmers, women, and marginalized communities. However, millions of eligible citizens miss out on these benefits simply because they don't know the schemes exist, or they find official gazette notifications too complex to understand.*
> 
> *Our goal was to build a single-window civic platform that matches citizens with government welfare schemes with **100% legal eligibility accuracy**, while using AI to personalize recommendations and assist users in both English and regional languages like Tamil."*

---

### [0:45 – 1:30] 2. The Core Problem & Our Two-Tier Solution
> *"Existing portals like MyScheme or state websites act mostly as basic keyword search engines. They do not evaluate whether a citizen is legally eligible before showing a scheme.*
> 
> *If an AI system hallucinates or guesses that a student qualifies for an old-age pension or a farmer loan, it wastes the citizen's time and money. That is why our system is built on a strict **Two-Tier Architecture**:*
> 
> 1. *First, we have a **Deterministic Eligibility Engine** written strictly in Python rule logic. It mathematically checks statutory criteria like age, income ceiling, gender, education, social category, and state of residence. AI is never allowed to guess legal eligibility.*
> 2. *Second, once the citizen is proven legally eligible, our **AI Recommendation Engine** powered by GPT-4o-mini prioritizes the schemes based on the citizen's urgent needs, occupational match, and application deadlines."*

---

### [1:30 – 3:30] 3. Live Demonstration Sequence
*(Action: Start at the Landing Page `http://localhost:5173` on screen)*

> *"Let us walk you through the live working system.*
> 
> *Here on the **Landing Page**, you can see our clean citizen interface. Notice our verified database counter: we have **62 real Tamil Nadu State Government schemes** loaded in our Supabase PostgreSQL database, complete with statutory eligibility rules and 314 required documents.*
> 
> *(Action: Click 'Sign In' and log in as our demo student. Note: Use a temporary test account; credentials are not stored in project files.)*
> 
> *Now, we navigate to the **Citizen Profile**. Here, our user has set their age as 19, gender as Female, occupation as Student, education as Higher Secondary, and resident state as **Tamil Nadu** (`state_id = 23`), with district set to **Chennai**.*
> 
> *(Action: Click 'Recommendations' in the top navigation bar)*
> 
> *When we open the **Recommendations Page**, the backend immediately executes our geographic pre-filter and evaluates all 62 schemes. Notice what appears:*
> 
> *Here in the main grid, we see top recommended schemes like **Moovalur Ramamirtham Ammiyar Higher Education Assurance Scheme** (also known as Pudhumai Penn).*
> 
> *(Action: Point to the Eligibility Badge and Match Score on the card)*
> 
> *Notice an essential architectural principle here: the green badge says **ELIGIBLE**, and right next to it is an **85% Match Score**. We want to emphasize that the **Match Score is NOT a percentage of eligibility**. You are either legally eligible or not; the 85% score represents AI priority and urgency."*

---

### [3:30 – 4:15] 4. Explainable AI & Three-State Decision Logic
*(Action: Click 'View Eligibility Criteria' or open the rejection test scenario)*

> *"Our system provides full transparency. When the citizen clicks on the eligibility details, they see an itemized checklist:*
> - *Age: PASS (19 is within the permitted range)*
> - *Gender: PASS (Female satisfies scheme requirement)*
> - *State: PASS (Tamil Nadu matches state restriction)*
> 
> *Now, what happens if an ineligible user applies?*
> *If a 25-year-old male citizen views this scheme, our engine immediately flags it as **NOT_ELIGIBLE** in red, stating clearly: 'Citizen gender MALE does not match required FEMALE'. There is zero guesswork.*
> 
> *(Action: Scroll down to 'Schemes Requiring Demographic Verification')*
> 
> *Furthermore, real government schemes often have statutory clauses that cannot be checked from basic demographics—for example, possessing a single-girl child certificate or holding agricultural land. Instead of falsely rejecting or falsely approving the citizen, our engine cleanly categorizes these as **POSSIBLY_ELIGIBLE**, highlighting the exact clauses that require departmental verification."*

---

### [4:15 – 5:00] 5. Scheme Details, Documents, and Official Links
*(Action: Click 'View Full Details' on a scheme)*

> *"Opening the **Scheme Details Page**, we see the administering department, financial benefits, and application guidelines.*
> 
> *Take a look at the **Required Documents** section. In government data, some documents are explicitly mandatory, while others are optional or unconfirmed in the gazette. Rather than misleading the citizen, our UI tags unconfirmed items as **'Requirement Unspecified'**.*
> 
> *Most importantly, when the citizen clicks **'Visit Official Portal'**, our system strictly directs them to verified government domains (`.gov.in` or `.nic.in`). We filter out third-party blog links to protect citizens from phishing.*
> 
> *(Action: Click the Bookmark icon, then navigate to 'Saved Schemes')*
> 
> *Citizens can bookmark schemes to their **Saved Schemes** library and receive automated deadline notifications as application closing dates approach."*

---

### [5:00 – 6:00] 6. Multilingual Conversational Chatbot
*(Action: Open the floating Chatbot in the bottom-right corner)*

> *"To make this accessible to citizens of all digital backgrounds, we integrated a **Conversational NLP Assistant**.*
> 
> *(Action: Type in English: 'I am a college student in Tamil Nadu. What schemes can I apply for?')*
> 
> *When we ask in English, the chatbot reads the citizen's profile context, executes the deterministic engine, and provides clear, tailored scheme options.*
> 
> *(Action: Type in Tamil: 'நான் தமிழ்நாட்டில் படிக்கும் மாணவி. எனக்கு என்ன கல்வி உதவித்தொகை கிடைக்கும்?')*
> 
> *Now watch this: we submit the exact same query in **Tamil**. The assistant automatically detects Tamil, retrieves the matching schemes, and replies in natural, grammatically correct Tamil.*
> 
> *Crucially, the chatbot is completely stateless. It cannot modify or corrupt the user's database profile, and it uses the exact same eligibility rules as the main portal."*

---

### [6:00 – 6:45] 7. Security, Testing & Architecture
> *"Behind the scenes, our system is built for enterprise-grade security:*
> - *We use **Supabase PostgreSQL** with **Row-Level Security (RLS)**. No user can view or edit another citizen's profile or saved schemes.*
> - *All sensitive API keys—including our Supabase Service-Role key, OpenAI key, and Parse API key—exist strictly on the backend. The frontend bundle contains zero secret credentials.*
> - *Our system is verified by **247 passing backend unit tests** in Pytest, **20 passing frontend tests** in Vitest, **clean Oxlint linting**, and a successful production build."*

---

### [6:45 – 7:15] 8. Conclusion
> *"In summary, we have built a functional, secure, and explainable Government Scheme Recommendation System.*
> 
> *We have piloted this system with **62 live, real-world Tamil Nadu welfare schemes**, proving that combining a deterministic rule engine with multilingual generative AI can solve a genuine civic challenge.*
> 
> *Thank you very much. We are now open to any questions from the committee."*
