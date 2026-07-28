---
name: e2e-evaluator
description: Playbook for running end-to-end evaluation and verification of Telescopic Text expansions before git push.
triggers:
  - "e2e test"
  - "run evaluation"
  - "pre-push check"
  - "eval"
---

# E2E Evaluation Playbook

Use this playbook to perform end-to-end verification of the AI Telescopic Text application after running unit tests and before executing a `git push`.

## Step-by-Step Procedure

1. **Verify Backend Health & Configuration**:
   - Confirm server starts cleanly with `uv run python app.py`.
   - Send HTTP GET to `http://127.0.0.1:8000/api/config` and verify valid JSON array of `models`.

2. **Execute E2E Expansion Test**:
   - Send HTTP POST to `http://127.0.0.1:8000/api/expand` with test payload:
     ```json
     {
       "sentence_with_blank": "I stepped into the _ room.",
       "provider": "anthropic",
       "model": "claude-haiku-4-5-20251001",
       "api_key": "<USER_KEY>"
     }
     ```
   - Verify response contains `"replacement"` key with bracketed trigger words (e.g. `[[quiet]]`).

3. **Verify Frontend Assets**:
   - Ensure `static/style.css` and `templates/index.html` render cleanly without browser console errors.

4. **Approval**:
   - If all steps pass without errors, proceed to `git push`.
