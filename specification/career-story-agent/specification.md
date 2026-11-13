# Specification: career-story-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Bootstrap agent code in `assets/career-story-agent/`
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

- [x] Create `assets/career-story-agent/app/skills/career-story/SKILL.md` — guides the agent through the full career story workflow:
  - Step-by-step instructions: (1) retrieve data from all career-data tools, (2) assemble context, (3) synthesise narrative, (4) identify strengths and skill gaps, (5) generate 2–3 next steps
  - Guardrail rules embedded in the skill: never surface compensation data, never make promotion/performance promises, always ground strengths and gaps in specific data points, always present exactly 2–3 next steps
  - Sparse data handling: if one or more tools return no data, proceed with available data and state what was missing
  - Tone guidance: professionally encouraging — factual and specific, not generic or vague

---

## Project-Specific Tasks

### Data Retrieval — career-data MCP Tools (14 tools)

All retrieval is read-only via the `career-data` mock MCP server. In production, these tools connect to SuccessFactors via principal propagation.

- [x] `get_employee_profile` — biographical data, job info, org position; compensation fields excluded
- [x] `get_job_info` — current position, department, location, cost centre
- [x] `get_employment_info` — hire date, employment type, FTE, assignment
- [x] `get_manager_info` — direct manager name, title, department
- [x] `list_goals` — active and completed goals with status and progress
- [x] `list_development_goals` — IDP development goals
- [x] `list_skills` — skill name, proficiency level, date added
- [x] `get_performance_review` — latest completed review; rating, narrative, manager comments
- [x] `list_performance_reviews` — all completed reviews summary list
- [x] `list_learning_activities` — completed and in-progress courses; overdue filter supported
- [x] `list_certifications` — active certifications with status and expiry
- [x] `list_achievements` — spot awards and recognition entries
- [x] `list_role_skills` — required skills for current role (may return empty)
- [x] `tell_my_story` — single aggregated career narrative call

### Career Story Synthesis

- [x] Core `generate_career_story` logic in `agent.py` — calls tools, assembles context, synthesises via LiteLLM:
  - Personalised career narrative covering journey, achievements, completed learning, goals met
  - Strengths section: 2–4 key strengths anchored to specific data points
  - Skill gaps section: 1–3 gaps linked to stated goals or role requirements
  - Next steps section: exactly 2–3 specific, immediately actionable next steps
- [x] Compensation exclusion guardrail — never reference salary, pay grade, bonus, equity
- [x] No-promotion-promise guardrail — never state, imply, or predict a promotion outcome or target role likelihood
- [x] Own-data-only guardrail — refuse requests about another person's data
- [x] Sparse data handling — proceed with available data, state which sources were unavailable

### Privacy & Guardrails

- [x] All MCP tool calls pass the authenticated user's identity token (principal propagation)
- [x] Prompt-layer check: verify retrieved records belong to the authenticated user
- [x] Strictly read-only — no create, update, or delete operations exposed

---

## Mock Data (DEMOCO — Jane Smith, user 100045)

Demo employee for preview and testing:
- **Profile**: Jane Smith, Finance Analyst, Finance dept (FIN), New York, hired 2021-06-14
- **Manager**: John Lee (100001), VP Finance, Finance, New York
- **Goals**: G-100045-1 Automate monthly close (Completed 100%), G-100045-2 SAP Analytics Cloud cert (On Track 60%), G-100045-3 Mentor intern (Completed 100%)
- **Skills**: Financial Analysis (Advanced), FP&A Modelling (Advanced), SAP Analytics Cloud (Intermediate), Data Storytelling (Beginner)
- **Performance**: PR-2025 rating 4.0 Exceeds Expectations; PR-2024 rating 3.5 Meets Expectations
- **Learning**: LMS-FIN-201 (Completed), LMS-SAC-110 (Completed), LMS-LEAD-101 (In Progress), LMS-COC-2026 (Completed)
- **Achievements**: ACH-100045-1 Process Improvement, ACH-100045-2 Innovation, ACH-100045-3 Recognition (Finance Rookie of the Year)
- **Certification**: CERT-SAC-100045 SAP Analytics Cloud (In Progress)

---

## Business Instrumentation

- [x] Structured logging and OpenTelemetry spans for all five PRD milestones:
  - M1 `career_story.data_retrieval` — SuccessFactors/career-data tools retrieved
  - M2 `career_story.narrative_synthesis` — career narrative synthesised
  - M3 `career_story.strengths_gaps` — strengths and skill gaps identified
  - M4 `career_story.next_steps` — next steps presented
  - M5 `career_story.employee_action` — employee acts on a next step
- [x] `bootstrap(app)` called after `app = server.build()` in `main.py`

---

## Testing

- [x] `conftest.py` sets `IBD_TESTING=true` — agent runs with mock MCP tool results
- [x] Unit tests in `assets/career-story-agent/tests/`:
  - `test_get_employee_profile.py` — profile fields present, compensation fields absent
  - `test_get_skills.py` — skill name and proficiency level returned
  - `test_get_goals.py` — goal name, status, progress returned
  - `test_get_performance_reviews.py` — narrative/comments returned, exact DEMOCO text
  - `test_get_learning_history.py` — course name and completion date returned, overdue filter
  - `test_get_career_development_plan.py` — achievements and certifications returned
  - `test_guardrails.py` — compensation terms never appear; other-employee requests refused; no promotion implications
- [x] Integration test: end-to-end `invoke` with all tools mocked — assert narrative, strengths, skill gap, 2–3 next steps
- [x] `pytest` coverage ≥ 70% (actual: 90%)
- [x] `test_report.json` exists in `assets/career-story-agent/`
