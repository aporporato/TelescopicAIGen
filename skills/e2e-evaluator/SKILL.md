---
name: e2e-evaluator
description: Playbook and automated runner for end-to-end evaluation of Telescopic Text expansions before git push.
triggers:
  - "e2e test"
  - "run evaluation"
  - "pre-push check"
  - "eval"
---

# E2E Evaluation Playbook & Automated Runner

Use this skill to execute end-to-end verification of the AI Telescopic Text application.

## Automated Execution Command
To run the automated E2E evaluation test suite:
```bash
uv run python skills/e2e-evaluator/run_e2e.py
```

## Procedures Verified by the Script
1. **API Endpoint & Config Verification**: Verifies `GET /api/config` returns active model configurations.
2. **Validation & BYOK Security Verification**: Verifies `POST /api/expand` enforces sentence blanks (`_`) and in-memory API key requirements.
3. **Live HTTP Server Verification**: Launches the live FastAPI server on `http://127.0.0.1:8000` and validates real socket HTTP requests.
