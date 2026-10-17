# AI Council Project Handoff

Prepared 2026-10-17 for Claude. This is a status-oriented handoff of the conversation, repository, decisions, and next steps; it is not a verbatim transcript.

For detailed codebase architecture, launch behavior, implementation gaps, and safe continuation guidance, see [CLAUDE_HANDOFF.md](CLAUDE_HANDOFF.md).

## Start Here

The workspace contains an AI Council project intended to coordinate specialized LLM agents through requirements, design, implementation, testing, deployment, monitoring, and maintenance. The current practical objective is to make a Gardening Planner app a sample project and use its requirements plus dummy data to functionally test the Epic Architect workflow.

Do not assume that the sample Gardening Planner requirements or Epic output already exist. They have been discussed but not yet saved. First complete the requirement inputs in the dependency order below, then run/test Epic Architect.

## Repository State

- Workspace/repository: `AI_Council` at `/Users/chancehooper/Documents/Code Projects/AI_Council`.
- Current Git branch: `ai-council-agents`.
- HEAD: `80cb2e5` (`Initial commit for AI Council agents`).
- Worktree at last check: modified `business_analyst.agent.md`, `epic_architect.agent.md`, `qa_planner.agent.md`, and `technical_architect.agent.md`; a modified nested repository/submodule appears at `../BloomingMarvellousApp`.
- Do not discard or overwrite those existing changes. The BloomingMarvellous app is outside this workspace and should be treated as the reference product/source for reverse-engineering, not as disposable data.
- The repository also contains Python council/orchestration files, prompts, output folders, `MultiAgentCouncil/`, and project notes. This handoff does not claim those components have been tested.

## Existing Agent and Reference Files

- [Business Analyst Agent](business_analyst.agent.md): BDAT-based elicitation, council roster, human approval gates, stated technical constraints, and Jira/Confluence documentation guidance.
- [Epic Architect Agent](epic_architect.agent.md): groups stories into Epics/milestones, prioritizes, maps dependencies, and includes Jira/Confluence documentation guidance.
- [Technical Architect Agent](technical_architect.agent.md): proposes architecture, data model, APIs, and infrastructure; includes Jira/Confluence documentation guidance.
- [QA Planner Agent](qa_planner.agent.md): test strategy, test cases, and traceability; includes Jira/Confluence documentation guidance.
- [Discovery survey](requirements/discovery_survey_questions.md): the current saved generic stakeholder questionnaire.
- No other files were present in `requirements/` when checked. In particular, no gardening sample requirements, personas, journeys, Epic Architect output, QA artifacts, or dummy data have been saved yet.

Only these four `.agent.md` definitions currently exist in the workspace. The larger Council roster has been specified in conversation, but the other specialist agents have not been created as `.agent.md` files here.

## Product and Council Intent

The Council should turn business-stakeholder input into requirements and then coordinate agents that design, build, test, deploy, monitor, and maintain iOS apps and websites/backends. Stated implementation preferences include Python, Swift for iOS, Java for websites, AWS, Lambda APIs, S3 static assets, Terraform, GitHub automation, and OpenAPI where appropriate.

The envisioned additional roles are Data Architect, UI Designer, Front End Developer, Back End Developer, CI/CD Agent, QA Tester, Stress-Tester, Data Security Architect, Security Architect, Security Tester, Monitoring Agent, and Infrastructure Agent. These are desired roles, not all implemented agents.

Human approval gates requested:

1. Approve BA-produced user journeys and project assets.
2. Approve the solution architecture.
3. Agree on data governance and data security policies through stakeholder review.
4. Review UI designs and approve before implementation handoff.
5. Review every test build and pass/fail it before promotion.
6. Make a human production go/no-go decision.

The BA is expected to create actionable backlog tasks and stakeholder-readable reference material. The stakeholder prefers guided, non-technical discovery followed by conversational clarification, with HTML deliverables where useful. Agent documentation is intended to be persisted in Jira and Confluence via MCP; the agent files contain this instruction, but no Jira issues or Confluence pages have yet been verified as created.

## Gardening Planner Sample Requirements Captured

Use the existing BloomingMarvellous app as the basis for reverse-engineering where its code or product behavior is available. Do not invent features and present them as verified BloomingMarvellous behavior; mark inferred or proposed behavior explicitly and validate it against the app/stakeholder.

Four subscription personas/access profiles were described:

| Profile | Garden details and conditions | Recommendation library |
| --- | --- | --- |
| Casual / Free | Basic garden-level light (shade/light), moisture (wet/normal/very dry), soil type (sandy/rocky/loamy/clay/peaty), and postcode/location | Free plant library across flowers, shrubs, herbs, fruits, and vegetables |
| Floral Gardener | One or more gardens, with conditions specified per bed; includes soil pH (acid/neutral/alkaline), shelter (under cover/sheltered/normal/exposed), drainage (slow/average/fast), and other relevant conditions | Free library plus paid flowers and shrubs |
| Allotment Gardener | One or more gardens, with conditions specified per bed; same expanded bed conditions | Free library plus paid herbs, fruits, and vegetables |
| Pro | Expanded garden/bed conditions | Both paid decorative plants and paid food-growing plants, plus free library |

The product goal is to suggest suitable plants based on garden conditions and subscription entitlements. Do not assume details such as exact recommendation ranking, bed dimensions, calendar features, alerts, image identification, social/community features, or purchase flows without evidence or an explicit assumption.

## Governance and Technical Constraints Stated

- All data storage and handling must comply with GDPR.
- The BA should ask stakeholders about other applicable, industry-specific non-functional/regulatory requirements in plain language.
- Stakeholder wants a Lambda-based API and dedicated S3 static asset storage. A JSON/file-based data layer was requested, with ACID behavior where needed; this is a preference/request that the Technical Architect must validate rather than assume S3 itself provides transactional ACID semantics.
- Monitoring/scaling preference: scale up within an 80% maximum-load threshold; when vertical scaling is exhausted, scale out; scale in one at a time when the remaining `n-1` capacity can handle load below 80%, with minimum `n=1`. The Monitoring and Infrastructure agents must translate this into AWS-appropriate measurable metrics and behavior; Lambda concurrency does not map directly to a fixed pool of Lambda instances.
- App Store Connect credentials are project-specific and should only be requested when needed. Do not put credentials or secrets in Jira, Confluence, Markdown, source control, or prompts.
- Security baseline includes OWASP. Free/open-source security testing tools were requested.

## Conversation and Planning History

- The four current agent files were drafted: Business Analyst, Epic Architect, Technical Architect, and QA Planner.
- The BA reference survey was saved to `requirements/discovery_survey_questions.md`.
- Jira/Confluence via MCP was requested for agent documentation. Instructions were added to all four existing agent files. The Technical Architect and QA Planner files currently contain duplicate Documentation bullets; consider cleaning these only if editing those files for another reason.
- A request was made to create a separate branch from `/Root` for AI Council apart from BloomingMarvellous. The current branch `ai-council-agents` and initial commit exist, but this handoff does not establish whether the branch was created from the intended `/Root` or whether the app separation is complete. Verify Git ancestry/layout before making further repository changes.
- The user asked to reprioritize tasks so persona descriptions come first, and all sample-requirements synthesis happens before building/testing Epic Architect. That reordering was proposed but the global task list was not reliably reconciled. Use the ordered plan below as the operative plan.
- A prior attempt to create this handoff using a disabled file-creation tool failed. This file is the actual saved handoff.

## Operative Task List (Dependency Ordered)

### A. Prepare a grounded Gardening Planner requirements packet

1. **Draft persona descriptions** for Casual/Free, Floral Gardener, Allotment Gardener, and Pro from the captured tier/access rules. Mark unknowns and assumptions; avoid repeating the full brief in later artifacts.
2. **Reverse-engineer BloomingMarvellous** using the available app/repository and record observed capabilities separately from assumptions. The nested app repository already appears modified; preserve its changes.
3. **Define the minimum feature/module scope** supported by verified product behavior and the four persona profiles.
4. **Map core user journeys** (onboarding/garden setup, bed conditions where entitled, plant recommendations, and subscription access only where confirmed or explicitly marked as proposed).
5. **Capture cross-cutting and non-functional requirements**: GDPR, security, accessibility, performance, availability, location/postcode handling, and any stakeholder-specific regulations. Ask only material unresolved questions.
6. **Create a compact source-of-truth requirements packet** in `requirements/` with personas, scope, journeys, data/information needs, assumptions, and traceable acceptance criteria. Avoid maintaining duplicate prose in multiple files.
7. **Create realistic, clearly synthetic dummy data** derived from that packet (e.g. users/subscriptions, gardens/beds/conditions, and a small categorized plant catalogue). Include cases that exercise all tier entitlement boundaries and at least one unsuitable plant. Do not use real personal data.
8. **Publish/link approved artifacts to Jira and Confluence via MCP as appropriate**, after confirming the correct project/space and structure. Report any unavailable MCP integration or required destination instead of claiming upload succeeded.

### B. Build and functionally test Epic Architect

9. **Define a small acceptance checklist and expected result** for Epic Architect using the requirements packet and dummy data.
10. **Run Epic Architect once** on the finalized packet, producing prioritized Epics, one-interaction/function-sized stories, dependencies, and acceptance criteria. Keep input bounded to the source-of-truth packet.
11. **Compare output to the acceptance checklist**, record gaps, and make only targeted corrections. Save the result and link/publish it in Jira/Confluence as appropriate.

### C. Continue downstream only after the Epic output is accepted

12. Technical Blueprinting (Technical Architect), incorporating Data Architect and security/governance requirements.
13. QA Plan Generation (QA Planner), traceable to accepted stories and criteria.
14. Expand the remaining Council agents and CI/CD, test, deployment, monitoring, and infrastructure workflows as a separate implementation phase.

## Current Progress

- Agent definitions: **4 present** (BA, Epic Architect, Technical Architect, QA Planner).
- Generic discovery questionnaire: **saved**.
- Gardening Planner persona set: **captured in conversation, not yet saved as a requirements artifact**.
- Gardening feature scope and journeys: **not yet validated or documented**.
- Gardening Epic/User Story output: **not created**.
- Dummy test data and Epic Architect acceptance test: **not created/run**.
- Technical blueprint and QA plan for the Gardening sample: **not started**.
- Jira/Confluence documentation: **agent guidance exists; successful MCP publication is unverified/not done**.

## Suggested First Action

Start with task A1: create the four concise persona descriptions from the captured table, then inspect BloomingMarvellous to ground the feature scope. Keep confirmed product observations, stakeholder requirements, and assumptions clearly separated throughout.