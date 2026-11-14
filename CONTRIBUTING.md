# Contributing

Keep changes scoped to this repository and use synthetic data. Do not add client exports, credentials, private database snapshots or personal environment dependencies.

Explain the business failure being addressed and the resulting behavior. Changes to authorization, target effects, approval binding, admission idempotency or workflow ordering need a regression that demonstrates the violated invariant. Documentation-only changes do not require a heavy model or load run.

Before proposing a change:

```bash
uv sync --frozen
uv run ruff check .
uv run pytest -q
uv run python scripts/export_contracts.py
git diff --exit-code -- contracts
uv run python scripts/secret_scan.py --working-tree --output evidence/runs/review-worktree.json
```

Retain real histories before changing workflow code. Run the relevant qualification profile against a clean source commit and preserve raw failures as well as successes. Report whether a check used a real service, a test double, or was blocked. A valid JSON response, live process or clean scanner result is not a business acceptance result.

Do not tune prompts on the held-out corpus. A new development iteration after looking at held-out results needs a new separately frozen evaluation partition; retain the previous comparison. Keep the runbook competent and give it the same observations and downstream execution path as the model.

All GitHub text is written in English. Reviews should identify concrete risks and evidence, not claim independent human approval when the same automation authored and reviewed a change. The maintainer's repository licence decision is still pending; do not add or change a licence or public visibility implicitly.
