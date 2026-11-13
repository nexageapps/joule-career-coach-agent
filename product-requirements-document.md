# Product Requirements Document (PRD)

**Title:** Career Story Agent  
**Date:** 2026-11-13  
**Owner:** HR / People Development  
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**
Employees hold a wealth of career data in SAP SuccessFactors — goals, performance feedback, completed learning, achievements, and development plans — but rarely experience it as a coherent story. This agent reads all of that data for the signed-in employee and returns a personalised, professionally encouraging career narrative that surfaces their strengths, names their skill gaps, and offers 2–3 concrete next steps they can act on today.

**Business Need:**
Employees struggle to connect the dots across their own HR data. Goals set last year, performance feedback from reviews, completed training, and development plans live in separate modules and are rarely seen together. This fragmentation leads to disengagement, underutilisation of SuccessFactors, and missed career development opportunities. Without a clear picture of their journey, employees are less likely to take ownership of their development or initiate career conversations with their manager.

**Expected Value:**
- More employees maintain up-to-date development goals in SuccessFactors (target: 30% → 45% within 90 days)
- More career conversations between employees and managers (target: 1 → 2 per year per employee within 90 days)
- Higher learning completion rates as employees connect courses to their personal gaps (target: 60% → 70% within 90 days)

**Product Objectives (Prioritised):**
1. Enable every employee to receive a personalised, accurate career story generated from their live SuccessFactors data in a single interaction
2. Surface each employee's strengths and skill gaps clearly, grounded in real data, not generalisations
3. Present 2–3 specific, immediately actionable next steps that connect to available learning, goals, or career conversations
4. Enforce strict data privacy: only the signed-in employee's own data is ever accessed or surfaced

---

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Employees with up-to-date development goals | 30% | 45% | 90 days post-launch | Career Development / Goal Management | user |
| Career conversations per employee per year | 1 | 2 | 90 days post-launch | Identify and Grow Talent | user |
| Learning course completion rate | 60% | 70% | 90 days post-launch | Educate and Develop Talent | user |

---

## User Profiles & Personas

### Primary Persona: Alex — Individual Employee

Alex is a 34-year-old mid-level professional who has been with the company for four years. He logs into SuccessFactors occasionally to complete mandatory tasks — updating a goal before the review cycle, acknowledging a performance form — but has never felt that the system tells him anything meaningful about his own development. He knows he has a performance review document from last year and has completed several learning courses, but he couldn't tell you how those things connect to where he wants to go. He is moderately comfortable with technology, uses Slack and Microsoft Teams daily, and would engage with an AI assistant if it gave him something genuinely useful in under five minutes. His biggest frustration is that career development feels like it's something HR does to him, not something he owns.

**Goals:**
- Understand where he stands in his career today, in plain language
- Know what he is good at and what he needs to develop
- Leave with one clear thing to do next, not a list of vague suggestions

**Key Tasks:**
- Ask the agent to generate his career story
- Review his strengths and skill gaps
- Pick a next step and act on it (start a course, update a goal, schedule a conversation)

---

### Secondary Persona: Sam — People Manager

Sam manages a team of eight and holds monthly 1-on-1s with each direct report. Career conversations are the ones she finds hardest to prepare for — she needs to review each person's goals, latest performance form, and learning activity before the meeting, which takes 20–30 minutes per person. She values structured conversations but often arrives underprepared. She is not the primary user of this agent but would use it to help a direct report generate their career story before or during a career conversation.

**Goals:**
- Be better prepared for career conversations without spending significant preparation time
- Help her team members articulate their own development story, not have it told to them

**Key Tasks:**
- Encourage direct reports to use the agent before their 1-on-1
- Reference the agent's output during career conversation to structure the discussion

---

### Secondary Persona: Jordan — HR Business Partner

Jordan supports three business units as an HR Business Partner and regularly coaches employees through development planning. He needs to quickly understand an employee's career context — their history, goals, and gaps — before advising them. Currently he manually reviews multiple SuccessFactors modules, which is time-consuming and inconsistent. He would use the agent alongside an employee to help them see themselves more clearly.

**Goals:**
- Quickly understand an employee's career context to give relevant, personalised advice
- Help employees articulate their strengths and development areas in a development planning session

**Key Tasks:**
- Ask the agent to generate a career story with an employee present
- Use the output as the starting point for a development planning conversation

---

## Product Principles

1. **Own story, own voice:** The agent reflects the employee's actual data back to them — not benchmarks, not generic career paths. Every output is specific to that individual.
2. **Encourage without overpromising:** The tone is professionally encouraging. The agent does not make promotion or performance promises, does not share compensation, and does not predict outcomes.
3. **Privacy as the foundation:** The agent can only access and surface data belonging to the authenticated user. This is enforced at both the API and prompt level and is non-negotiable.
4. **Action over reflection:** Insight without action has no value. Every interaction must end with at least one concrete, specific next step the employee can take.
5. **Simplicity first:** The agent must be usable in a single conversation without onboarding, training, or reading a manual.

---

## Business Context

**Current State:**
Employees interact with SAP SuccessFactors across multiple modules — Employee Central, Performance & Goals, Learning, Succession & Development, Skills Management, and Opportunity Marketplace — but experience these as separate tools, not a connected career picture. Career conversations are infrequent (approximately once a year) and often underprepared. Development goals are only current for approximately 30% of employees. Learning completion sits at 60%, partly because employees do not connect available courses to their personal skill gaps.

**Strategic Alignment:**
This solution supports the organisation's talent development strategy by increasing employee ownership of career growth, improving quality and frequency of career conversations, and driving utilisation of existing SuccessFactors investments. It aligns with the Recruit to Retire E2E process, specifically the "Develop to Grow" phase covering talent education (BPS-388) and talent identification and growth (BPS-389).

---

## Goals and Non-Goals

### Goals (In Scope)

- Generate a personalised career narrative for the signed-in employee using live SuccessFactors data (profile, goals, performance reviews, skills, learning, achievements, career plans)
- Identify and clearly surface the employee's key strengths, grounded in their data
- Identify and clearly surface the employee's skill gaps relative to their goals or role
- Present 2–3 concrete, specific next steps the employee can act on immediately
- Enforce data isolation: only the authenticated employee's own data is ever accessed or returned
- Exclude compensation data at all layers (API query, context assembly, and agent response)
- Support use by employees (self-service), managers (pre-conversation preparation), and HR Business Partners (development planning sessions)

### Non-Goals (Out of Scope)

- Surfacing, estimating, or referencing compensation data of any kind
- Making promotion decisions, predictions, or recommendations
- Providing performance ratings, scores, or rankings
- Accessing or displaying any data belonging to another employee
- Writing back to SuccessFactors (this is a read-only agent at launch)
- Replacing the performance management or goal-setting process
- Providing career path benchmarking against external market data

---

## Requirements

### Must-Have Requirements

**REQ-01: Career Story Generation**

- **Problem to Solve:** Employees cannot see a coherent picture of their career journey across their SuccessFactors data without manually navigating multiple modules.
- **User Story:** As an employee, I need to ask the agent to generate my career story so that I receive a clear, personalised narrative of my journey, achievements, and growth in a single interaction.
- **Acceptance Criteria:**
  - Given I am authenticated, when I ask the agent for my career story, then it retrieves data from my profile, goals, performance reviews, skills, learning history, and career plans in SuccessFactors.
  - Given my data has been retrieved, when the agent synthesises the narrative, then the output covers my journey to date, highlights key achievements, and reads as professionally encouraging.
  - Given insufficient data exists for one or more modules, when the agent responds, then it generates the best possible narrative from available data and explicitly notes what was missing.
- **Maps to Objective:** Objective 1
- **Priority Rank:** 1

---

**REQ-02: Strengths Identification**

- **Problem to Solve:** Employees rarely have a clear, data-grounded view of what they are genuinely good at, which limits their ability to build on those strengths or articulate them.
- **User Story:** As an employee, I need the agent to identify my key strengths from my SuccessFactors data so that I can understand and articulate what I bring to my role and my team.
- **Acceptance Criteria:**
  - Given my career story has been generated, when strengths are surfaced, then each strength is grounded in at least one specific data point (e.g. a goal achieved, a skill endorsed, a performance comment).
  - Given strengths are presented, when I read them, then they are stated clearly, specifically, and without vague language such as "hard worker" or "team player" unless supported by specific evidence.
- **Maps to Objective:** Objective 2
- **Priority Rank:** 2

---

**REQ-03: Skill Gap Identification**

- **Problem to Solve:** Employees do not know which skills they need to develop to reach their career goals, leaving them unable to focus their learning or development efforts effectively.
- **User Story:** As an employee, I need to understand my skill gaps relative to my stated goals or role so that I can focus my development efforts where they will have the most impact.
- **Acceptance Criteria:**
  - Given my goals and skills data are available, when skill gaps are identified, then each gap is explicitly connected to a stated goal or role requirement.
  - Given a skill gap is surfaced, when presented to me, then it is described constructively and without negative framing.
- **Maps to Objective:** Objective 2
- **Priority Rank:** 3

---

**REQ-04: Actionable Next Steps**

- **Problem to Solve:** Employees leave reflection conversations without a clear action, meaning insight does not translate into development activity.
- **User Story:** As an employee, I need the agent to present 2–3 specific, immediately actionable next steps so that I leave every interaction with something concrete to do.
- **Acceptance Criteria:**
  - Given a career story has been generated, when next steps are presented, then there are exactly 2–3 of them, each specific and actionable (e.g. names a specific course, suggests updating a specific goal, or recommends scheduling a career conversation).
  - Given next steps are presented, when I review them, then each step is directly linked to a strength to build on or a skill gap to address.
- **Maps to Objective:** Objective 3
- **Priority Rank:** 4

---

**REQ-05: Data Privacy — Own Data Only**

- **Problem to Solve:** Employees must trust that the agent cannot access or surface another employee's data, and that their own data cannot be accessed by others through the agent.
- **User Story:** As an employee, I need to know that the agent only accesses my own data so that I can trust it with my career information.
- **Acceptance Criteria:**
  - Given I am authenticated, when the agent retrieves SuccessFactors data, then it uses principal propagation to ensure only my employee record is accessible.
  - Given any attempt to request another employee's data, when the agent processes the request, then it refuses and explains it can only access the signed-in user's own data.
- **Maps to Objective:** Objective 4
- **Priority Rank:** 5

---

**REQ-06: Compensation Data Exclusion**

- **Problem to Solve:** Compensation data is sensitive and legally protected in many jurisdictions; surfacing it accidentally would breach trust and potentially compliance requirements.
- **User Story:** As an employee and as the organisation, I need compensation data to never appear in any agent response so that privacy and compliance are maintained.
- **Acceptance Criteria:**
  - Given any SuccessFactors data retrieval, when the agent assembles context, then compensation-related fields (salary, pay grade, bonus, equity) are excluded at the API query layer.
  - Given any agent response, when reviewed, then no compensation figure, pay band, or salary reference appears under any circumstances.
- **Maps to Objective:** Objective 4
- **Priority Rank:** 6

---

**REQ-07: No Promotion or Performance Promises**

- **Problem to Solve:** Employees may interpret agent outputs as commitments from the organisation; this must be explicitly prevented to avoid legal or HR risk.
- **User Story:** As the organisation, I need the agent to never make promotion decisions, performance judgements, or career promises so that employees understand it is a reflective tool, not an evaluative one.
- **Acceptance Criteria:**
  - Given any interaction, when the agent responds, then it never states, implies, or predicts a promotion outcome, performance rating, or career guarantee.
  - Given the agent identifies next steps, when presented, then they are framed as suggestions the employee can choose to act on, not commitments from the organisation.
- **Maps to Objective:** Objective 4
- **Priority Rank:** 7

---

### High-Want Requirements

**REQ-08: Graceful Handling of Sparse Data**

- **Problem to Solve:** Some employees have limited data in SuccessFactors (e.g. new joiners, employees who rarely update their profiles), which could result in a thin or unhelpful career story.
- **User Story:** As a new or less active SuccessFactors user, I need the agent to still provide useful output even when my data is sparse so that I am not excluded from the experience.
- **Priority Rank:** 1

---

**REQ-09: Conversational Follow-Up**

- **Problem to Solve:** A single generated output may not answer all of an employee's questions about their career story.
- **User Story:** As an employee, I need to be able to ask follow-up questions about my career story — such as "tell me more about my skill gaps" or "what courses are available for this gap" — so that I can explore my narrative interactively.
- **Priority Rank:** 2

---

### Nice-to-Have Requirements

**REQ-10: Session Summary Export**

- **Problem to Solve:** Employees may want to reference their career story, strengths, gaps, and next steps outside the agent session.
- **User Story:** As an employee, I need to save or copy a summary of my career story session so that I can refer to it later or share it with my manager before a career conversation.
- **Priority Rank:** 1

---

## Non-Functional Requirements

### Performance
- **Latency:** Initial career story generation (data retrieval + synthesis) should complete within 30 seconds for 95% of requests.
- **Throughput:** The agent must support concurrent sessions without degradation; designed for organisation-wide self-service use.

### Reliability
- **Availability:** Aligned to SAP BTP SLA for the deployed runtime.
- **Fallback:** If one or more SuccessFactors modules are unavailable, the agent generates the best narrative from available data and communicates clearly what was missing.

### Explainability
- **Traceability:** Each strength or skill gap identified by the agent is linked to the specific SuccessFactors data point that informed it.
- **Decision Logging:** All tool calls (data retrieval and narrative synthesis steps) are logged via OpenTelemetry spans tied to defined milestones.
- **Uncertainty Communication:** When data is insufficient to make a strong statement, the agent qualifies its output clearly rather than fabricating detail.

---

## Solution Architecture

**Architecture Overview:**
A Python A2A agent deployed on SAP BTP retrieves employee data from SAP SuccessFactors via a set of custom MCP tools (one per SuccessFactors data domain), assembles a structured context, and uses an LLM via SAP Generative AI Hub to synthesise the career narrative and next steps. Principal propagation ensures data isolation per authenticated user.

**Key Components:**

- **Career Story Agent (Python, A2A protocol):** Core agent that orchestrates data retrieval, context assembly, LLM reasoning, and response generation.
- **SuccessFactors MCP Tools (custom):** A set of MCP tools — one per data domain — that call SuccessFactors OData/REST APIs using principal propagation. Covers: Employee Profile, Skills & Competencies, Performance Reviews, Goals, Learning History, Career Development Plans.
- **SAP SuccessFactors (all modules):** Source of truth for all employee career data — Employee Central, Performance & Goals, Learning, Succession & Development, Skills Management, Opportunity Marketplace.
- **SAP Generative AI Hub (LLM):** Provides the language model used for narrative synthesis, strengths/gap analysis, and next step generation.
- **SAP BTP (runtime):** Hosting environment for the agent and MCP tools.

**Integration Points:**

- SuccessFactors OData APIs (Employee Central, Performance & Goals, Succession & Development): read-only, per-user, via principal propagation
- SuccessFactors REST APIs (Performance Management, Continuous Performance): read-only, per-user, via principal propagation
- SuccessFactors Learning API: read-only, learning history and completions
- SAP Generative AI Hub: LLM inference for narrative generation

---

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
The agent is designed with extension points to support future capabilities without structural rework:
- Additional SuccessFactors data sources can be added as new MCP tools without modifying the core agent
- The system prompt is structured to allow domain-specific guardrails to be updated independently
- The context assembly layer is modular: each data domain contributes a discrete context block, allowing new domains to be added cleanly

**Business Step Instrumentation:**
All five business milestones are instrumented with structured OpenTelemetry log statements. Each milestone emits a log on achievement and on miss/skip to support production observability and debugging. Log statements follow the pattern: `[MILESTONE_ID].[achieved|missed]: [description]`.

---

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent (LLM-driven reasoning over retrieved data)

**Actions the agent performs without human approval:**
- Retrieval of the authenticated employee's SuccessFactors data across all configured modules
- Assembly of a structured context from retrieved data
- Generation of a personalised career narrative, strengths summary, skill gap analysis, and next steps
- Responding to conversational follow-up questions within the same session

**Actions that require human review or approval:**
- None — the agent is read-only. It never writes to SuccessFactors or takes action on behalf of the employee.

**Model or engine used:** LLM via SAP Generative AI Hub (model selection per deployment configuration)

**Knowledge & data sources accessed:**

- SAP SuccessFactors Employee Central: biographical data, job information, organisational position
- SAP SuccessFactors Performance & Goals: goal plans, performance review forms, continuous performance data
- SAP SuccessFactors Learning: completed courses, learning assignments, certifications
- SAP SuccessFactors Succession & Development: career development plans, development activities
- SAP SuccessFactors Skills Management: skills profile, skill levels, skill endorsements
- SAP SuccessFactors Opportunity Marketplace: talent marketplace activity (where available)

**Tools or connectors invoked:**

- `get_employee_profile` MCP tool: retrieves biographical data and job information from Employee Central (read-only)
- `get_skills` MCP tool: retrieves the employee's skills profile from Skills Management (read-only)
- `get_performance_reviews` MCP tool: retrieves completed performance review forms and ratings context from Performance & Goals (read-only; compensation fields excluded at query level)
- `get_goals` MCP tool: retrieves active and completed goal plans from Performance & Goals (read-only)
- `get_learning_history` MCP tool: retrieves completed courses and certifications from Learning (read-only)
- `get_career_development_plan` MCP tool: retrieves career development plans and activities from Succession & Development (read-only)

**Guardrails & fail-safes:**

- Compensation data (salary, pay grade, bonus, equity) is excluded at the API query layer and re-validated at the prompt layer — never surfaced under any circumstances
- The agent never makes promotion decisions, performance predictions, or career guarantees
- The agent refuses any request to access another employee's data; principal propagation enforces this at the API layer
- If an individual SuccessFactors module is unreachable, the agent proceeds with available data and discloses the gap transparently
- LLM responses are constrained by a system prompt that defines tone, scope boundaries, and prohibited content; this prompt is treated as a configuration artefact and versioned alongside the agent

---

## Governance, Risk & Compliance

**Data Handling:**
- The agent operates exclusively on data belonging to the authenticated user; no cross-user data access is permitted at any layer
- Compensation fields are excluded at the API query layer; the agent prompt explicitly prohibits compensation references
- No employee data is stored by the agent beyond the active session; SuccessFactors remains the system of record
- PII accessed during a session is handled in accordance with the organisation's existing SuccessFactors data processing agreements

**Compliance Frameworks:**
- GDPR: the agent reads existing employee data under the same consent framework as SuccessFactors; no new data collection occurs
- Internal HR data classification policies apply; the agent must be classified as an HR tool with appropriate access controls

**Approval Flows:**
- The agent takes no high-risk automated actions (it is read-only); no approval flows are required at runtime
- System prompt updates (guardrail changes) require review by HR and legal before deployment

---

## Milestones

### M1: SuccessFactors Data Retrieved

- **Description:** The agent has successfully called all configured SuccessFactors MCP tools and assembled a complete (or best-available) context for the authenticated employee.
- **Achieved when:** All configured MCP tool calls complete and at least the employee profile and one additional data domain return data successfully.
- **Log on achievement:** `M1.achieved: SuccessFactors data retrieved successfully for employee session; modules_loaded=[profile, goals, reviews, skills, learning, career_plan]`
- **Log on miss:** `M1.missed: SuccessFactors data retrieval failed or returned insufficient data; modules_failed=[<list>]`

---

### M2: Career Narrative Synthesised

- **Description:** The LLM has generated a coherent career narrative covering the employee's journey, achievements, and growth based on the assembled context.
- **Achieved when:** A narrative of meaningful length is generated and passes basic content validation (references specific data points, not generic text).
- **Log on achievement:** `M2.achieved: Career narrative synthesised successfully; narrative_length_tokens=<n>`
- **Log on miss:** `M2.missed: Career narrative synthesis failed or produced insufficient output; reason=<reason>`

---

### M3: Strengths and Skill Gaps Identified

- **Description:** The agent has identified and surfaced at least one strength and at least one skill gap, each grounded in a specific data point from the employee's SuccessFactors record.
- **Achieved when:** The response includes a named strength with a data reference and a named skill gap with a goal or role reference.
- **Log on achievement:** `M3.achieved: Strengths and skill gaps identified; strengths_count=<n>; gaps_count=<n>`
- **Log on miss:** `M3.missed: Could not identify strengths or skill gaps; likely cause=insufficient_data`

---

### M4: Next Steps Presented

- **Description:** The agent has presented 2–3 specific, actionable next steps linked to the employee's strengths or gaps.
- **Achieved when:** The response contains exactly 2–3 next steps, each referencing a specific action (a named course, a goal to update, or a conversation to schedule).
- **Log on achievement:** `M4.achieved: Next steps presented; steps_count=<n>`
- **Log on miss:** `M4.missed: Next steps not presented or were non-specific; steps_count=<n>`

---

### M5: Employee Acts on a Next Step

- **Description:** The employee engages with at least one of the presented next steps within the agent session (e.g. confirms they will act, asks for more detail on a specific step, or follows a recommended link).
- **Achieved when:** The employee's follow-up message references or engages with one of the presented next steps.
- **Log on achievement:** `M5.achieved: Employee engaged with next step; step_referenced=<step_description>`
- **Log on miss:** `M5.missed: Employee ended session without engaging with next steps`

---

## Risks, Assumptions, and Dependencies

### Risks

- **API availability:** All 14 discovered SuccessFactors APIs are currently marked unavailable in this environment. API access and principal propagation configuration must be completed before the agent can operate on live data. This is the highest-risk item for the initial delivery timeline.
- **Data quality dependency:** The quality of the career story is directly proportional to the completeness of the employee's SuccessFactors data. Employees with sparse profiles, outdated goals, or no performance reviews will receive a less rich narrative. A parallel change management effort to improve data quality is recommended.
- **LLM output quality:** Narrative tone and specificity depend on LLM behaviour, which must be validated with representative data before go-live. Prompt engineering and testing with real SuccessFactors data profiles is required.
- **Employee trust:** Employees must trust that their data is private and that the agent cannot make career decisions about them. Clear communication of scope and guardrails is essential at launch.

### Assumptions

- All listed SuccessFactors modules (Employee Central, Performance & Goals, Learning, Succession & Development, Skills Management, Opportunity Marketplace) are live and populated with employee data at go-live.
- Principal propagation between SAP BTP and SAP SuccessFactors can be configured for this tenant.
- SAP Generative AI Hub is available and accessible from the BTP deployment environment.
- The agent is consumed via a conversational interface (e.g. embedded in an HR portal or standalone chat); the specific front-end channel is out of scope for this PRD.

### Dependencies

- SAP SuccessFactors API access provisioning and principal propagation configuration
- SAP Generative AI Hub tenant setup and model selection
- SAP BTP runtime environment for agent deployment
- SuccessFactors data quality baseline (measured before launch, as agreed)

---

## Open Questions

- Which conversational front-end channel will employees use to access the agent (e.g. SuccessFactors embedded, Microsoft Teams, standalone BTP UI)?
- Should the agent support multiple languages, and if so, which are required at launch?
- Is there a requirement to log or audit the career stories generated for HR governance purposes, and if so, what retention period applies?
- Will managers or HR Business Partners use the agent on behalf of an employee, or only alongside them? This affects whether the data isolation model needs to accommodate any form of delegated access.

---

## Appendix

### Glossary

- **A2A protocol:** Agent-to-agent communication protocol used by SAP BTP AI agents, enabling standardised invocation and response handling.
- **MCP tool:** Model Context Protocol tool — a function exposed to the agent that it can call to retrieve data or perform actions.
- **Principal propagation:** An SAP BTP mechanism that forwards the authenticated user's identity to downstream systems (here, SAP SuccessFactors), ensuring that API calls are made in the context of that user and can only access their own data.
- **Career story:** The agent's synthesised output — a personalised narrative covering the employee's journey, strengths, skill gaps, and next steps, generated from their live SuccessFactors data.

### References

- SAP SuccessFactors Performance & Goals API: `sap.sf:apiResource:PerformanceandGoalsPMGM:v1`
- SAP SuccessFactors Employee Central Profile API: `sap.sf:apiResource:ECEmployeeProfile:v1`
- SAP SuccessFactors Skills Management API: `sap.sf:apiResource:ECSkillsManagement:v1`
- SAP SuccessFactors Succession & Development API: `sap.sf:apiResource:SuccessionandDevelopmentSD:v1`
- SAP SuccessFactors Performance Management REST API: `sap.sf:apiResource:PMGMPerformanceREST:v1`
- RBA Sub-processes: Educate and develop talent (BPS-388), Identify and grow talent (BPS-389)
