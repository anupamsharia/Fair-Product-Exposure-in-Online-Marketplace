# FairCart Backend Tools

`backend/tools/` keeps non-runtime scripts out of the backend app root.

- `maintenance/` updates or seeds backend data.
- `diagnostics/` inspects database or ML state without changing runtime code.
- `manual_tests/` contains request scripts and manual validation helpers.
- `experiments/` keeps exploratory scripts and dataset tooling.

Run these from the repo root or from `backend/`. The moved scripts now resolve the backend root automatically.
