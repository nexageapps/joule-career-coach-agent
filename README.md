<p align="center">
  <img src="docs/images/banner.png" alt="Career Coach Agent, SAP Joule Studio + SuccessFactors" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT licence"></a>
  <img src="https://img.shields.io/badge/SAP-Joule%20Studio-0a6ed1" alt="SAP Joule Studio">
  <img src="https://img.shields.io/badge/SAP-SuccessFactors-0a6ed1" alt="SAP SuccessFactors">
  <img src="https://img.shields.io/badge/MCP-read--only-2ea44f" alt="MCP read-only">
  <img src="https://img.shields.io/badge/deploy-open%20item-orange" alt="Deployment open item">
</p>

# SuccessFactors Career Coach Agent

This is the SAP Joule Studio solution export for the SuccessFactors Career Coach Agent (`career-story-agent`).

The agent turns an employee's own SuccessFactors record into a short career story: strengths, skill gaps, and two or three next steps.

It is a Joule Studio export, not a standalone product.

Full write-up on SAP Community: [SuccessFactors Already Knows Your Career Story. Here's How I Built the Joule Studio Agent.](https://community.sap.com/t5/artificial-intelligence-blogs-posts/successfactors-already-knows-your-career-story-here-s-how-i-built-the-joule/ba-p/14522283)

## How it was built

**1. Describe the intent.** Joule Studio turns a plain description into an intent document.

<img src="docs/images/02-creating-intent.gif" alt="Creating the intent in Joule Studio" width="100%">

**2. Answer the design questions.** Tone, modules and success metrics.

<img src="docs/images/04-selecting-tone.gif" alt="Selecting the agent tone" width="100%">

**3. Generate the solution.** Joule Studio writes the specification, skills, tests and MCP provider config.

<img src="docs/images/06-generate-solution.gif" alt="Generating the solution" width="100%">

## Testing

Joule Studio generates and runs three test suites for the agent: structure tests, server tests and agent tests.

| Total tests | Passed | Failed | Coverage | Score |
|---|---|---|---|---|
| 215 | 215 | 0 | 89.81% | 100% |

<img src="docs/images/07-testing-overview.gif" alt="Joule Studio testing overview, 215 of 215 tests passed" width="100%">

## What it looks like

| Career story from DEMOCO data | Guardrail in action |
|---|---|
| <img src="docs/images/12-preview-democo-story.png" alt="Preview with DEMOCO career story"> | <img src="docs/images/13-preview-guardrail.png" alt="Guardrail refusing salary talk"> |

## Repo layout

| Path | What it holds |
|---|---|
| `solution.yaml` | Joule Studio solution manifest |
| `intent.md` | The agent's intent |
| `product-requirements-document.md` | Generated requirements |
| `specification/` | Solution and agent specification |
| `assets/career-story-agent/app/` | Agent app, skills and MCP providers |
| `assets/career-story-agent/tests/`, `prebuilt_tests/` | Tests |
| `assets/career-story-agent/mcp-mock.json` | DEMOCO mock data for preview |

## Mock data

The export previews against DEMOCO mock data through `assets/career-story-agent/mcp-mock.json`. It does not include a live SuccessFactors connection, and no credentials are stored here.

## Guardrails

The agent only uses read-only tools. Compensation tools and write tools are excluded. It does not discuss salary or make promotion or performance promises, and it only reads the employee's own data.

## Deployment status

Deployment on SAP Build is currently blocked by a 5-minute pre-validation timeout. That is still an open item.

<img src="docs/images/15-deploy-timeout.png" alt="Deploy pre-validation timeout" width="100%">

## Use it

1. Import the export into your own SAP Joule Studio tenant.
2. Point the MCP provider at your own SuccessFactors MCP server, or keep the mock for preview.
3. Run the tests, then preview before you deploy.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md).

## Licence

[MIT](LICENSE). SAP, SuccessFactors and Joule are trademarks of SAP SE. This project is not affiliated with SAP.

---

*Built by [NexageApps](https://nexageapps.com).*
