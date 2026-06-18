CLAUDE.md

Wiretap Development Instructions

This repository is designed for fully autonomous development.

The complete product specification already exists in:

wiretap-agent-docs/

Treat those documents as canonical.

Read them before making any architectural or implementation decision.

⸻

Canonical Documentation

Always use the following documents as the source of truth.

wiretap-agent-docs/00_AGENT_MISSION.md
wiretap-agent-docs/01_PRODUCT_SPEC.md
wiretap-agent-docs/02_ARCHITECTURE.md
wiretap-agent-docs/03_TECH_STACK.md
wiretap-agent-docs/04_REPO_STRUCTURE.md
wiretap-agent-docs/05_WORKER_API.md
wiretap-agent-docs/06_UI_SPEC.md
wiretap-agent-docs/07_IMPLEMENTATION_PLAN.md
wiretap-agent-docs/08_TASKS_FOR_AGENT.md
wiretap-agent-docs/09_DEFINITION_OF_DONE.md
wiretap-agent-docs/10_DECISION_POLICY.md
wiretap-agent-docs/11_README_DRAFT.md
wiretap-agent-docs/12_RISKS_AND_LIMITATIONS.md
wiretap-agent-docs/13_PROMPT_FOR_AGENT.md

If multiple documents overlap, prefer the most specific one.

⸻

Autonomous Mode

Operate autonomously.

Do not ask for implementation decisions.

Do not stop for confirmation.

When several reasonable solutions exist:

* evaluate alternatives
* choose one
* document the reasoning
* continue implementation

The human is responsible only for:

* running the application on macOS
* granting permissions
* manual validation
* reporting bugs

Everything else is your responsibility.

⸻

macOS Development

You are NOT expected to execute autonomously on macOS.

Instead:

* build portable code
* isolate macOS adapters
* provide mocks where necessary
* provide manual validation procedures

Do not claim macOS functionality is tested unless manually verified by the user.

Docker or Linux execution is NOT proof that macOS functionality works.

⸻

Quality Bar

Every implementation MUST include:

* unit tests
* integration tests where applicable
* regression tests for discovered bugs
* documentation updates

No feature is complete without tests.

No exception.

⸻

Security Requirements

Security is mandatory.

Never introduce:

* shell injection
* SQL injection
* unsafe subprocess execution
* unsafe deserialization
* path traversal
* hardcoded credentials
* embedded secrets

Always:

* parameterize SQL
* validate inputs
* sanitize paths
* use safe subprocess APIs
* pin dependencies
* minimize external packages

Run security tooling where applicable.

⸻

Static Analysis

Code MUST pass before completion:

* ruff
* mypy
* pytest

Do not suppress failures.

Fix them.

⸻

Documentation

Every architectural change must be reflected in documentation.

README must always match actual behavior.

Do not document planned features as implemented.

⸻

Git

Prefer small logical commits.

Commit messages must clearly describe intent.

Avoid generic messages like:

* fix
* update
* changes
* misc

The agent is expected to create local commits.

The agent MUST NOT rely on git push permissions.

All commits should remain local until reviewed by the human.

The human is solely responsible for pushing commits to remote repositories.

The agent should commit frequently in small logical units with descriptive commit messages.

If a task is completed, commit it immediately.

Do not accumulate unrelated changes into one large commit.

Prefer many small reviewable commits over large commits.

⸻


Production Honesty

Never fake implementation.

Never fake benchmarks.

Never fake tests.

Never claim validation that did not happen.

Never hide failing tests.

Never disable tests to make CI green.

⸻

Priority Order

1. Correctness
2. Security
3. Maintainability
4. Simplicity
5. Performance
6. Developer convenience

When uncertain, choose the more maintainable solution.
