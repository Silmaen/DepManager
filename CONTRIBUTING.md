# Contributing to DepManager

Thanks for your interest! The full contributor guide — local setup, coding
conventions, how to run the tests, the release checklist — lives in
[`docs/contributing.md`](docs/contributing.md).

## Quick start

```bash
poetry install
poetry run pytest
```

## Reporting issues

Use the GitHub issue tracker:
<https://github.com/Silmaen/DepManager/issues>. Pick the "Bug report" or
"Feature request" template — they prompt for the information we need to
reproduce or scope the work.

## Submitting a pull request

1. Fork, branch off `main`.
2. Keep changes focused — one PR, one concern.
3. Run `poetry run pytest` and `poetry run black --check src test` locally
   before pushing.
4. Follow the PR template (fills in automatically when you open the PR).
5. Describe *why* in the PR body; the *what* is visible in the diff.

## Security issues

Do not open a public issue for security reports. See
[`SECURITY.md`](SECURITY.md).

## Code of conduct

Be decent. We're all here to build useful software; assume good faith, keep
feedback technical, and don't punch down.
