# Career Story Agent

SuccessFactors Career Coach Agent

## Business challenge

Help employees understand their own career journey by turning their SuccessFactors profile, goals, performance reviews, skills, learning, and achievements into a clear, encouraging personal career story — with identified strengths, skill gaps, and 2–3 practical next steps. The agent works only with the signed-in employee's own data, never shares compensation information, and never makes promotion or performance promises.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Employees with up-to-date development goals | 30% | 45% | 90 days post-launch | Career Development / Goal Management | user |
| Career conversations per employee per year | 1 | 2 | 90 days post-launch | Identify and Grow Talent | user |
| Learning course completion rate | 60% | 70% | 90 days post-launch | Educate and Develop Talent | user |

## Key Milestones

1. **Data retrieval** — Employee opens the agent and their SuccessFactors data (profile, goals, performance reviews, skills, learning history, achievements) is successfully retrieved.
2. **Career story synthesis** — Agent synthesises the retrieved data into a personalised, coherent career narrative covering their journey to date.
3. **Strengths & skill gaps identified** — Agent surfaces the employee's key strengths and identifies skill gaps relative to their goals or role.
4. **Next steps presented** — Agent presents 2–3 concrete, actionable next steps (e.g. a recommended learning course, scheduling a career conversation, updating a development goal).
5. **Employee acts** — Employee saves or acts on at least one next step within the agent session.

## Business Architecture (RBA)

### End-to-End Process

Recruit to Retire

### Process Hierarchy

```
Recruit to Retire
└── Develop to Grow (generic)
    └── Educate and develop talent (generic) [BPS-388]
        └── Develop skills and competencies
    └── Identify and grow talent (generic) [BPS-389]
        └── Plan career development
```

### Summary

The challenge maps to the "Develop to Grow" phase of the Recruit to Retire E2E, specifically the "Educate and develop talent" and "Identify and grow talent" sub-processes — with industry variants for Internal Workforce and Public Sector.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
|------------------------|-------------------------|------------|-------------------|--------------------|--------------------|---------------------|------|---------------------|
| Retrieve employee profile & biographical data | SAP SuccessFactors Employee Central | `sap.sf:apiResource:ECEmployeeProfile:v1` | — | — | — | — | Yes | API not available in current environment; MCP tool must be custom-built |
| Retrieve skills and competencies | SAP SuccessFactors Platform | `sap.sf:apiResource:ECSkillsManagement:v1` | — | — | — | — | Yes | API not available; custom MCP tool required |
| Retrieve performance review data | SAP SuccessFactors Performance & Goals | `sap.sf:apiResource:PMFormsManagement:v1`, `sap.sf:apiResource:PMGMPerformanceREST:v1` | — | — | — | — | Yes | API not available; custom MCP tool required |
| Retrieve employee goals | SAP SuccessFactors Performance & Goals | `sap.sf:apiResource:PerformanceandGoalsPMGM:v1` | — | — | — | — | Yes | API not available; custom MCP tool required |
| Retrieve learning history and completions | SAP SuccessFactors Learning | — | — | — | — | — | Yes | No API ORD ID surfaced; learning data retrieval via SuccessFactors Learning API |
| Retrieve career development plans | SAP SuccessFactors Succession & Development | `sap.sf:apiResource:SuccessionandDevelopmentSD:v1` | — | — | — | — | Yes | API not available; custom MCP tool required |
| Synthesise career narrative with strengths, gaps, next steps | Custom AI Agent (no standard SAP asset covers narrative generation) | — | — | — | — | — | Yes | Core gap — requires custom Python AI agent with LLM reasoning |
| Enforce data privacy (own data only, no compensation) | SuccessFactors principal propagation + agent guardrails | — | — | — | — | — | Maybe | Principal propagation must be configured; compensation fields explicitly excluded in agent prompt |

### Key findings

- All 14 relevant SuccessFactors APIs were identified but are marked **unavailable** in this environment — MCP tools for SuccessFactors data access must be custom-built.
- No pre-built MCP servers exist for SuccessFactors APIs; the agent will call SuccessFactors OData/REST APIs via custom MCP tools with principal propagation to ensure data isolation.
- The primary custom development is a Python A2A agent that orchestrates multi-source SuccessFactors data retrieval and synthesises a personalised career story using LLM reasoning.
- Compensation data must be explicitly excluded at both the API query layer and the agent prompt layer to meet the stated privacy constraint.
- SAP SuccessFactors Performance & Goals, Succession & Development, Learning, Platform, and Opportunity Marketplace are all in use — full module coverage supports a rich career narrative.
- Tone should be a mix of professional and encouraging — like a coach-informed career summary document.

## Recommendations

### AI-Powered Career Story Agent on SAP SuccessFactors

#### Executive Summary

Python A2A agent retrieving SuccessFactors data to generate a personalised career narrative.

#### Recommended Solution

A pro-code Python agent (A2A protocol) deployed on SAP BTP that retrieves employee data from SAP SuccessFactors (profile, goals, performance reviews, skills, learning, achievements, career plans) via custom MCP tools with principal propagation, then uses LLM reasoning to synthesise a personalised career story — highlighting strengths, skill gaps, and 2–3 actionable next steps. The agent enforces strict data privacy: it only accesses the signed-in employee's own data, never exposes compensation, and never makes promotion or performance promises.

#### Problem Statement

Employees often struggle to connect the dots across their own HR data — goals set last year, performance feedback, completed training, and career plans — into a coherent picture of where they are and where they could go. This leads to disengagement, underutilisation of SuccessFactors, and missed career development opportunities.

#### Affected User Roles

- Individual employees (primary users — self-service career reflection)
- Managers (secondary — to support and prepare for career conversations)
- HR Business Partners (secondary — to support employees in development planning)

#### Important factors

##### Personalisation at scale
The agent reads live SuccessFactors data for each employee, ensuring the career story is always current and specific to that individual — not a generic template.

##### Privacy and trust by design
Principal propagation ensures the agent can only retrieve data belonging to the authenticated user. Compensation fields are excluded at the query and prompt layers. This is foundational to employee trust in the tool.

##### Low friction to act
By presenting 2–3 concrete, specific next steps (e.g. "Start the SAP SuccessFactors Learning course on stakeholder communication", "Add a development goal for Q3"), the agent bridges the gap between reflection and action.

#### Potential risks

##### API availability
All 14 discovered SuccessFactors APIs are currently marked unavailable in this environment. API access must be provisioned and principal propagation configured before the agent can retrieve live data.

##### Data quality dependency
The career story is only as good as the data in SuccessFactors. Employees with incomplete profiles, outdated goals, or no performance reviews will receive a less rich narrative — a change management effort may be needed alongside the agent launch.

#### Recommended solution category

AI Agent

#### Intent fit
92%
