# Claude Project and Codebase Briefing

Prepared 2026-10-17. Read this file together with [session_summary.md](session_summary.md). This briefing adds codebase details and operational guidance; it is not a verbatim chat transcript.

## 1. Immediate Objective

Continue the AI Council project without losing the decisions from the prior conversation. The immediate product task is to prepare a grounded Gardening Planner sample from the BloomingMarvellous app, then use that compact requirements packet and synthetic fixture data to evaluate the Epic Architect workflow.

Important: there is no finished gardening requirements packet, no Epic Architect output, and no dummy dataset yet. The gardening personas and broad access rules exist only in the conversation and [session_summary.md](session_summary.md). Do not report these deliverables as complete until they are saved and reviewed.

## 2. Repository Snapshot and Safety

- Workspace: `/Users/chancehooper/Documents/Code Projects/AI_Council`.
- Current branch: `ai-council-agents`.
- Last observed HEAD: `80cb2e5` (`Initial commit for AI Council agents`).
- At last status check, the worktree included modifications to `business_analyst.agent.md`, `epic_architect.agent.md`, `qa_planner.agent.md`, and `technical_architect.agent.md`; `../BloomingMarvellousApp` appeared as a modified nested repository/submodule; `session_summary.md` was untracked. The current briefing will also be untracked until committed.
- Never revert, clean, reset, or overwrite the modified agent files or nested BloomingMarvellous repository. Inspect their diffs before touching them.
- A prior request said to branch AI Council from `/Root` separately from BloomingMarvellous. The current branch exists, but its ancestry and exact separation from `/Root` were not verified. Do not make branch/layout changes without checking first.
- `AICouncil.code-workspace` opens both `../BloomingMarvellousApp/BloomingMarvellous` and the AI Council directory. Treat them as separate projects.
- `rg` was unavailable in the observed shell. Use VS Code search/file tools or a portable alternative if needed.

## 3. What Exists in the Codebase

### Custom VS Code agent instruction files

Four `.agent.md` files are present:

- [business_analyst.agent.md](business_analyst.agent.md): BDAT (Business, Data, Automation, Technology) discovery; stakeholder questioning; Council roster; human approval gates; GDPR and stated architecture constraints; Jira/Confluence documentation instruction.
- [epic_architect.agent.md](epic_architect.agent.md): organizes stories into Epics and milestones, prioritizes by value/effort/risk, and maps dependencies; Jira/Confluence instruction.
- [technical_architect.agent.md](technical_architect.agent.md): high-level architecture, data model, APIs, and infrastructure; Jira/Confluence instruction.
- [qa_planner.agent.md](qa_planner.agent.md): test strategy, test cases, story traceability, and defect reporting; Jira/Confluence instruction.

These files are agent instructions, not Python agent implementations. They are not wired into the Python orchestration code. Only four of the desired Council roles are represented as VS Code agent files. The Tech Architect and QA Planner instructions contain duplicate Jira/Confluence bullets; this is minor cleanup, not a priority unless those files are otherwise edited.

### Requirements and project notes

- [requirements/discovery_survey_questions.md](requirements/discovery_survey_questions.md) is the only requirements artifact currently in the `requirements/` folder. It is a general non-technical discovery survey.
- [session_summary.md](session_summary.md) records the conversation decisions, gardening persona rules, status, and dependency-ordered next tasks.
- [Council_MVP_7_Day_Plan.md](Council_MVP_7_Day_Plan.md) describes a separate local Ollama/LangGraph MVP plan, including TDD suggestions. Treat it as a plan, not proof those steps or tests have been completed.
- [context.md](context.md) describes local Apple Silicon/Ollama assumptions and a Council architecture. It may not match every implementation detail; verify against code.
- `prompts/` and `out/` currently only contain `.gitkeep`; no prompt suite or saved model outputs were found.
- No Python test suite for the Council orchestration was found. Files named `qa_test_agent.py` are QA tooling, not unit tests of the project.

### Python implementation tracks (keep them distinct)

There are at least three separate prototypes in this repository. None currently implements the complete desired business-to-production Council.

1. **Generated LangGraph developer loop**: `MultiAgentCouncil/` is a modular pipeline scaffold originally produced by `CouncilBuilder.py` (since retired and removed; it remains in git history). Its entry point is `MultiAgentCouncil/StartCouncil.py`.
2. **Interactive LLM answer council**: [council.py](council.py) prompts a user, optionally loads a context file/directory, asks Qwen and Mistral for answers, obtains cross-critiques, then asks Llama to synthesize a verdict.
3. **Product backlog council**: [ProductOwner.py](ProductOwner.py) loads requirements from a path, asks Qwen and Mistral to draft prioritized user stories, cross-critiques both drafts, asks Llama to synthesize a MoSCoW backlog, and saves `backlog.md` (or a supplied output path).

Other root-level prototypes:

- [FirstDevBot.py](FirstDevBot.py): interactive/Tk UI-oriented development flow. It supports multiple language choices, file/folder pickers, test commands, generated-file writing, changelog handling, and Git setup/push routines. Review the remainder of this script before running; do not point it at the AI Council or BloomingMarvellous working trees casually.
- [devops_release_agent.py](devops_release_agent.py): release/backlog/SonarQube/GitHub automation prototype with Git branch and release operations. Do not run against a real repository until audited and made safe for dry-run use.
- [qa_test_agent.py](qa_test_agent.py): scans/clones a repository, runs static/security analysis integrations, and creates bug-list records. It can access repositories and external tools; audit before use.
- [code_quality_system.py](code_quality_system.py): source scanner and LLM audit/report generator.
- [ask_qwen.py](ask_qwen.py): sends one prompt file plus optional context files to local Ollama. Defaults to Qwen2.5-Coder, `num_ctx=8192`, temperature 0.2, and can save model output.
- Root [state_schema.py](state_schema.py) and [memory_manager.py](memory_manager.py) are simple generic helpers, separate from `MultiAgentCouncil`'s own `TypedDict` state and persistent Markdown memory manager.
- `sonarqube-26.9.0.129388/` is a bundled SonarQube distribution; it is not required merely to inspect or run the LangGraph scaffold.

## 4. LangGraph Scaffold: Actual Workflow

`MultiAgentCouncil/orchestrator.py` wires this fixed sequence:

1. `requirements_refiner` calls the Llama model to expand one story into specs and Given/When/Then criteria.
2. `security_hardening` calls Mistral to produce security standards.
3. `scrum_master` calls Llama to generate a 1-3 item JSON task backlog; malformed output falls back to one generic task.
4. `coder` calls Qwen to produce code and tests as `=== FILE: relative/path ===` blocks and writes them under `MultiAgentCouncil/workspace/<project_name>/`.
5. `qa_validator` runs a language-specific test command locally.
6. On QA failure, it loops back to the coder, capped at five coding attempts. On a pass or exhausted attempts it goes to `promotion_gate`.
7. `promotion_gate` sets `promotion_approved` based only on test status and sets `release_environment` to `dev`. It does not deploy, merge, or request a human production approval.

The graph uses `MultiAgentCouncil/state_schema.py` (`CouncilState` TypedDict) with fields for project, language, story, memory, specs, criteria, security standards, backlog, current task, generated source, test results, bug list, environment, promotion flag, and repair attempts.

### Launch requirements and behavior

`MultiAgentCouncil/StartCouncil.py`:

- Creates `MultiAgentCouncil/.venv` if missing.
- Checks/imports LangGraph and will run `pip install --upgrade langgraph` if not installed.
- Requires a running Ollama endpoint at `http://localhost:11434` and exact model tags: `llama3.1:8b`, `mistral:7b`, `qwen2.5-coder:7b`.
- Sets `OLLAMA_KEEP_ALIVE=0s` for the child process and launches `orchestrator.py`.

The orchestrator asks interactively for a user story and target language. It currently hardcodes `project_name` to `modular_billing_system`, defaults an empty story to a billing example, and accepts language values without validating supported choices. Running it will make Ollama calls and may create/modify files under the scaffold workspace. Do not treat it as the Epic Architect test harness.

### Notable implementation gaps/risks from inspection

- [MultiAgentCouncil/llm_client.py](MultiAgentCouncil/llm_client.py) sends Ollama requests with a timeout and `keep_alive=0`, but no `num_ctx` or generation options. The MVP plan calls for testing a minimum context size; this is not implemented in this client.
- Only LangGraph is installed by the launcher; no pinned requirements/lock file was found. Other language test runners (Node, Go) are assumed present if selected.
- The generated scaffold has no committed tests for its own graph, nodes, file-block parser, or test routing.
- `Coder` writes returned files under a workspace and filters absolute/path-escape paths, but does not clean stale generated files from prior attempts. Consider isolated temporary directories when adding tests.
- `scrum_master._parse_tasks` only checks that a JSON item has a truthy `title`; it does not validate descriptions or task count after parsing.
- The promotion gate is only a flag, not a release workflow or a real stakeholder gate.
- [memory_manager.py](MultiAgentCouncil/memory_manager.py) writes a global `Context.md` snapshot and appends a short `ChatHistory.md` audit entry. The history does not contain a full conversation transcript. The global context file is overwritten after runs.
- [memory_manager.py](memory_manager.py) at repository root annotates `List` without importing it. This is a static inspection finding and has not been confirmed by running diagnostics/tests.
- Do not conflate the Lambda/S3 target architecture for stakeholder app projects with the local Ollama/LangGraph execution environment for the AI Council itself.

## 5. Backlog and Epic Tools

`ProductOwner.py` is the closest existing runnable utility for producing a backlog, but it is not the same as `epic_architect.agent.md`:

- It loads a selected file or recursively reads `.txt`, `.md`, and `.log` files in a directory.
- It produces user stories in a strict template, MoSCoW priority, Given/When/Then acceptance criteria.
- It drafts with Qwen and Mistral, critiques each draft with the other model, and uses Llama as final synthesizer.
- It saves the final backlog to a Markdown file.
- It expects Ollama and those three local model names; there are no retry/timeout controls or automated tests in the inspected code.
- Its stories are not currently linked to Jira/Confluence, nor are there explicit Epic/milestone/dependency structures in its output requirements.

Thus, an Epic Architect functional evaluation needs an explicit execution method. Options: invoke the VS Code Epic Architect instruction against the compact requirements packet and fixtures; or build a small harness that uses the instruction/prompt. Do not claim `ProductOwner.py` tests Epic Architect unless its behavior/output contract is deliberately extended and tested for Epic grouping, prioritization, and dependency mapping.

## 6. Gardening Planner Requirements From Stakeholder

Treat the following as captured requirements; separate them from observations that still need reverse-engineering in BloomingMarvellous.

### Persona and entitlement profiles

| Profile | Garden data | Plant recommendation access |
| --- | --- | --- |
| Casual / Free | Garden-level location/postcode; light (shade/light), moisture (wet/normal/very dry), and soil (sandy/rocky/loamy/clay/peaty) | Free plant library across flowers, shrubs, herbs, fruits, and vegetables |
| Floral Gardener | Multiple gardens and bed-specific conditions; includes soil pH (acid/neutral/alkaline), shelter (under cover/sheltered/normal/exposed), drainage (slow/average/fast), plus any validated fields | Free plants plus paid flowers and shrubs |
| Allotment Gardener | Multiple gardens and bed-specific conditions; same expanded condition model | Free plants plus paid herbs, fruits, and vegetables |
| Pro | Expanded garden/bed conditions | Free library plus both paid decorative and food-growing plants |

The product goal is to suggest suitable plants for the user's conditions and subscription tier. Unknowns such as recommendation scoring, exact plant attributes, payment/subscription flow, bed dimensions, reminders/calendar, image recognition, and social features must be verified in BloomingMarvellous or labeled as proposed assumptions.

### Product, governance, and platform constraints

- Stakeholder-facing discovery starts as a guided survey written for nontechnical business stakeholders, then uses chat to clarify requirements; use diagrams/HTML when helpful.
- BA outputs should produce stakeholder-readable project assets and actionable tasks for downstream agents.
- GDPR compliance is mandatory for data storage and processing. Ask the stakeholder in nontechnical language about additional sector-specific regulation.
- OWASP is the minimum security baseline; open-source tools are preferred for vulnerability testing.
- Desired app outputs: Swift iOS app; Java website if applicable; Python for Council/backend code was stated, with AWS deployment, Lambda APIs, dedicated S3 static assets, Terraform, GitHub automation, and OpenAPI APIs where appropriate.
- A JSON/file-backed data layer was requested, with ACID guarantees where needed. This is not an implementation decision yet: architecture must validate appropriate transactional storage and avoid implying that S3 alone provides ACID transactions.
- Requested scaling behavior is expressed in terms of 80% load, scale up to a vertical limit, scale out beyond it, and remove one capacity unit at a time when remaining `n-1` capacity is below 80%, minimum one. Translate this to AWS Lambda's concurrency/metrics model before writing requirements as testable thresholds.
- Never store App Store Connect credentials or other secrets in Markdown, prompts, Jira, Confluence, or source control. Credentials may differ by project and should be requested only when actually needed.

### Human approval gates

1. Stakeholder approves BA HTML user journeys/assets.
2. Stakeholder approves Technical Architect HTML solution architecture.
3. Stakeholder iterates and agrees to HTML data-governance and data-security policies.
4. Stakeholder reviews UI Designer HTML and approves before developer handoff.
5. Stakeholder manually passes/fails each test build before environment promotion.
6. Human production go/no-go is mandatory.

## 7. Jira and Confluence

The user requested that all agents use Jira and Confluence via MCP for documentation. The four existing agent instruction files mention this. No actual Jira project/issue or Confluence space/page has been confirmed or published yet. When tools are available:

- Discover/confirm the Jira project and Confluence space before creating content.
- Keep Jira for actionable Epics/stories/tasks/bugs and Confluence for durable narrative specs, architecture, governance, and stakeholder deliverables.
- Link artifacts bidirectionally and maintain stable IDs/traceability.
- Do not claim publication succeeded until the MCP tool reports success.
- Do not upload credentials or secrets.

## 8. Recommended Continuation Plan

Keep work dependency-ordered and do not build the Epic output from incomplete sample data.

### Phase A: Create a grounded sample requirements packet

1. Draft the four persona descriptions and entitlement matrix from Section 6. Keep them concise and state assumptions explicitly.
2. Inspect BloomingMarvellous in the other workspace folder. Record verified screens, user actions, data captured, plant categories/attributes, subscription behavior, and existing user journeys. Preserve its dirty worktree. If source is unavailable or opaque, label findings as unverified and ask the stakeholder only material questions.
3. Reconcile product observations with the captured persona rules. Identify discrepancies instead of silently choosing one.
4. Specify minimum feature modules and journeys from verified evidence. Do not import generic gardening-app features without evidence.
5. Specify acceptance criteria and NFRs for GDPR, authorization/tier access, privacy, usability/accessibility, performance, reliability, and location/postcode data as applicable. Separate confirmed requirements, assumptions, and questions.
6. Save a single compact source-of-truth packet under `requirements/` (suggested `gardening_planner_requirements.md`) with personas, scope, journeys, data/information requirements, assumptions/questions, and traceable acceptance criteria. Avoid duplicating the full content across multiple documents.
7. Create synthetic fixtures (suggested JSON) for users/subscription tiers, gardens/beds/conditions, and a compact plant catalogue. Exercise all four access profiles, free-vs-paid category entitlements, condition matches and mismatches, missing/edge values, and ensure no real personal data is used.
8. Publish approved documentation to Jira/Confluence if MCP destination is configured; otherwise leave artifacts locally and note what destination is needed.

### Phase B: Define and test Epic Architect

9. Decide the Epic Architect execution path. The `.agent.md` instruction alone is not a local Python executable; `ProductOwner.py` is a different backlog tool. Choose a clear path and capture it in the test plan.
10. Write a compact acceptance checklist: coverage of requirements; correct entitlement distinctions; coherent Epic grouping; MoSCoW or agreed priority; small one-interaction/function stories; explicit Given/When/Then acceptance criteria; dependencies; no unsupported assumptions; traceability to requirement IDs.
11. Run the chosen Epic Architect once on the source-of-truth packet, with dummy data only where it validates output decisions. Save output to a stable Markdown artifact and create/link Jira issues as applicable.
12. Evaluate each checklist item, record defects/gaps, and make targeted revisions. Mark the Epic & Story Synthesis task complete only after review.

### Phase C: Continue the project pipeline

13. Use accepted Epics/stories to create the Technical Architect blueprint; resolve Lambda/storage/ACID/scaling decisions explicitly and include the Data Architect/security feedback loop.
14. Create a QA plan traceable to accepted stories, then implement QA Tester and security/stress tests as separate roles.
15. Only after technical/security design approval, implement development agents and the GitHub/Terraform/CI/CD/release workflows. Enforce stakeholder test-build and production approval gates.
16. Create the remaining agent instructions/implementations (Data Architect, UI Designer, Front End Developer, Back End Developer, CI/CD, QA Tester, Stress-Tester, Data Security Architect, Security Architect, Security Tester, Monitoring, Infrastructure) and define how they exchange versioned artifacts.

## 9. Working Rules for the Next Agent

- Start from the current repository status and inspect diffs before editing. Do not reset/revert user changes.
- Keep the app under test (BloomingMarvellous) separate from the Council implementation. Confirm paths and Git roots before file operations.
- Use one source-of-truth requirements artifact and pass references/IDs to later stages to minimize context duplication.
- Mark every claim as one of: confirmed in code/product, stakeholder-stated, inferred, or unresolved.
- Do not run scripts that perform Git commits/pushes, deployment, scanning with external credentials, or package installation without first auditing their effects and getting appropriate authorization.
- Do not assume Jira/Confluence integration is operational just because agent instructions mention MCP.
- The branch/worktree currently has user changes. Never silently stage or commit the work.
- Run narrow tests as soon as code changes are made. For the Markdown-only requirements phase, validate links/structure and ensure requirements, synthetic data, Epics, and acceptance criteria align.

## 10. Immediate Next Action

Begin with Phase A step 1: save the four persona descriptions/access matrix, then inspect BloomingMarvellous and document verified behavior. Do not generate the Epics yet. The requirement packet and synthetic fixtures must be completed first so the Epic Architect test has stable, traceable input.