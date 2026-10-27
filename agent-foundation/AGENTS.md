# Agent Foundation — Codex project instructions

> This repository is a reusable **Agent application foundation** (Python / LangChain / LangGraph), not the Codex runtime. Codex is the development partner. Start at `CODEX_START_HERE.md`; follow its task-specific pointers. Before creating, updating or retiring project documentation, read `docs/current/文档维护.md`.

## Mission
- Create independent business Agents through configuration, instructions, services, tools and evals rather than copying the agent loop.
- Evolve `foundation/` only for capabilities demonstrably reusable across multiple agents.
- Treat this as a teaching project: explain what comes from libraries and what we implement.

## Inspect first, don't hallucinate capabilities
1. Inspect the relevant source, config and tests before planning or writing.
2. Distinguish **implemented / available in dependency / planned / unverified** in every analysis.
3. Read `docs/current/设计决定.md` (the reuse decision and its links) before proposing a new platform component. Prefer public, maintained OSS over duplicating a framework feature.
4. Never claim model-level or end-to-end success from unit tests or mock traces.

## Ownership / architecture
- `foundation/`: shared runtime assembly, config, models, registry, execution, approval, minimal evaluation and scaffolding.
- `agents/<agent_name>/`: agent-specific config, instructions, tools, services, knowledge, skills, and eval cases.
- `docs/current/`: current topic owners reached through the main index; `history/`: prior documents and recovery provenance.
- Feature records reuse their current requirement/task owners; the main index identifies them. Do not infer current authority from a legacy feature path.
- `.agents/skills/`: repeatable workflows for **Codex**, not runtime Agent skills.

## Workflow with the product owner
For a nontrivial feature, discuss **expected behavior and observable success** before writing implementation:
1. State user goal and concrete examples; ask only truly blocking questions.
2. Read code and classify requirements: existing/extend agent/extend foundation/use OSS dependency.
3. Offer lean options and tradeoffs (time, quality, interoperability, ownership, licensing).
4. Update the existing requirement/test/task owners identified by the main index; use the documentation policy when a distinct new record is necessary.
5. For significant changes to shared `foundation/`, propose the design, impact and migration path first; proceed when the user accepts the plan.
6. After implementation: run feasible tests, show actual commands and evidence, explain limitations, and update docs/decisions.

When explicitly asked to implement a clear and bounded task, implement without unnecessary back-and-forth while preserving this contract.

## Engineering & security
- Choose the smallest correct design. One agent before multi-agent; deterministic code for exact calculations.
- Use existing LangChain/LangGraph primitives for loop, checkpointing, human approval, retries and middleware where appropriate.
- Tools must have explicit parameters, schemas, permissions and failure modes. Never hide consequential writes inside innocuous read tools.
- Approval defaults to deny on uncertain or missing confirmation; NEVER auto-approve in evaluations.
- Never log secrets, tokens or private user content by default. Never commit `.env` or generated credentials.
- Do not deploy, publish, push, submit actual tickets or invoke external state-changing operations without explicit approval.
- Avoid private library APIs unless no stable alternative exists and justify the exception.
- For new dependencies, verify current APIs and version compatibility; explain model/API cost separately from OSS license.
- If changing scaffolding/public extension contracts, update templates, docs and regression tests.

## Tests / local commands
- `python -m unittest discover -s tests -v` — offline code tests; does not prove LLM behavior.
- `python -m foundation.cli doctor support_insights` — check deps/config (not live connectivity).
- `python -m foundation.cli demo support_insights` — deterministic service demo (not Agent Loop).
- `python -m foundation.cli run support_insights --trace --message "分析最近7天主要投诉"` — live LLM with Ollama running.
- `python -m foundation.cli eval knowledge_helper` — live model behavior eval; can fail nondeterministically.
- `python -m foundation.cli scaffold my_agent` — new agent skeleton.

## Teaching / delivery format
Explain in Chinese, retain English technical terms:
- **Goal and acceptance**
- **Reuse / Build / Extend** (what is inherited and what is custom)
- **Files and why** (paths and design rationale)
- **Tests / traces observed** vs **not verified**
- **Alternatives / tradeoffs** and migration notes
- **Next experiment**

When improving shared foundation, verify existing `support_insights` and `knowledge_helper` remain working at their tested layer.
