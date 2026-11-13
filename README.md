# SuccessFactors Career Coach Agent

This is a reference copy of the SAP Joule Studio solution export for the SuccessFactors Career Coach Agent (`career-story-agent`).

It is a Joule Studio export, not a standalone product. The agent turns an employee's own SuccessFactors record into a short career story: strengths, skill gaps, and two or three next steps.

## Mock data

The export previews against DEMOCO mock data through `assets/career-story-agent/mcp-mock.json`. It does not include a live SuccessFactors connection.

## Guardrails

The agent is limited to read-only tools. Compensation tools and write tools are excluded. It should not discuss salary or make promotion or performance promises.

## Deployment status

Deployment on SAP Build is currently blocked by a 5-minute pre-validation timeout. That is still an open item.

## Blog

Write-up of the build, the issues we hit, and what is still open:

https://community.sap.com/t5/artificial-intelligence-blogs-posts/successfactors-already-knows-your-career-story-here-s-how-i-built-the-joule/ba-p/14522283
