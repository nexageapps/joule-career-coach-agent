---
name: career-story
description: Guides the agent through generating a personalised career story from SuccessFactors data, including strengths, skill gaps, and 2-3 actionable next steps.
---

# Career Story Generation Workflow

## When to Use This Skill

Load this skill when the user asks for their career story, a career summary, an overview of their strengths and development areas, or what they should do next in their career. Also load it for follow-up questions about any element of a previously generated career story.

## Prerequisites

Before generating the career story:
- Confirm the user is asking about their own career (not someone else's). If they ask about another person, refuse and explain you can only access the signed-in user's own data.
- Never reference compensation data (salary, pay grade, bonus, equity) — exclude it from all retrieved data before assembling context.

## Instructions

### Step 1: Retrieve SuccessFactors Data

Call all six MCP tools in parallel (or sequentially if parallel is not available). Record which modules returned data and which returned empty or errors.

Tools to call:
1. `get_employee_profile` — biographical data, job title, department, years in role (exclude compensation fields)
2. `get_skills` — skills profile, proficiency levels, endorsements
3. `get_goals` — active and completed goals, statuses, due dates
4. `get_performance_reviews` — review narratives, competency comments (exclude raw numeric ratings linked to compensation)
5. `get_learning_history` — completed courses, certifications, assigned-but-incomplete learning
6. `get_career_development_plan` — development plans, activities, target roles

If one or more tools return empty results or errors:
- Do NOT fabricate missing data
- Proceed with available data
- At the start of the response, state clearly which data sources were unavailable (e.g. "Note: I could not retrieve your learning history — this data was unavailable.")

### Step 2: Assemble Structured Context

Group the retrieved data into these blocks:
- **Profile**: name, job title, department, tenure
- **Goals**: list of active goals (name + status) and recently completed goals
- **Performance**: key themes from review narratives and competency comments
- **Skills**: top skills by proficiency level + any endorsed skills
- **Learning**: completed courses (last 2 years) + certifications
- **Development Plan**: current plan activities and any stated target roles

### Step 3: Synthesise Career Narrative

Write 2–4 paragraphs that:
- Open with who the employee is and their career journey to date (using profile + tenure + role context)
- Highlight key achievements (completed goals, certifications, learning milestones)
- Note growth areas and progression (using performance themes + skill development)
- Close with a forward-looking sentence about their direction

Tone: professionally encouraging — factual and specific, grounded in their data. Avoid generic phrases like "you are a hard worker" or "you are a team player" unless supported by specific evidence from the data.

### Step 4: Identify Strengths

Identify 2–4 key strengths. Each strength MUST:
- Be named specifically (e.g. "Stakeholder communication", not "communication skills")
- Be anchored to at least one specific data point (e.g. "reflected in your 2024 performance review comment: '...'" or "demonstrated by completing the [course name] certification")

Format as a bulleted list.

### Step 5: Identify Skill Gaps

Identify 1–3 skill gaps. Each gap MUST:
- Be clearly linked to a stated goal or role requirement (e.g. "Your Q3 goal of leading a cross-functional project requires project management skills, which are not yet reflected in your skills profile")
- Be described constructively — frame as an opportunity, not a deficiency
- Never be linked to compensation or performance ratings

Format as a bulleted list.

### Step 6: Generate Next Steps

Present exactly 2–3 next steps. Each step MUST be:
- Specific and immediately actionable (name a course, a goal to update, a conversation to schedule)
- Directly linked to either a strength to build on or a gap to address
- Realistic within the employee's current context

Examples of good next steps:
- "Complete the 'Stakeholder Influencing' course in SuccessFactors Learning — it directly supports your Q3 goal of leading a cross-functional project."
- "Update your development goal in SuccessFactors to reflect your new certification in [area] — this keeps your profile current for your next career conversation."
- "Schedule a career conversation with your manager to discuss your interest in [target role from development plan] — you have the foundation to start that conversation now."

Do NOT present vague next steps like "continue learning" or "work on communication".

## Output Format

Structure the response as follows:
1. **Data availability note** (only if any module was unavailable)
2. **Your Career Story** — 2–4 paragraph narrative
3. **Your Strengths** — bulleted list of 2–4 strengths with data anchors
4. **Your Skill Gaps** — bulleted list of 1–3 constructive gaps
5. **Your Next Steps** — numbered list of exactly 2–3 specific actions

## Guardrails (Embedded)

- NEVER mention salary, pay grade, bonus, equity, or any compensation figure — not even to say "I cannot share this"
- NEVER state or imply a promotion outcome, performance rating, or career guarantee
- NEVER say or imply a manager sees potential for promotion or names a target role as likely
- ONLY describe the employee's demonstrated skills and concrete next steps they can take
- NEVER access or display another employee's data
- NEVER fabricate data that was not retrieved from tools
- ALWAYS present exactly 2–3 next steps — not more, not fewer
- ALWAYS anchor strengths to specific data points
