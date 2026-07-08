---
name: pre-deploy-check
description: Verifies all project files and configurations are ready for production deployment.
---

# Pre-Deploy Check Skill

This skill ensures that the FastAPI URL Shortener is completely ready to be deployed (e.g., to Render or any other platform) without errors.

## How it works
When invoked, this skill will:
1. **Dependency & Security Check:** Check if `requirements.txt` is updated and scan for any known insecure library versions.
2. **Code Linting:** Ensure there are no leftover debug/print statements in production code and that the code follows PEP8 standards.
3. **Secrets Validation:** Validate that environment variables (like `ADMIN_PASSWORD_HASH`) are correctly referenced via `os.getenv` (No hardcoded secrets).
4. **Test Runner:** Run the automated test suite (e.g., `pytest`) to ensure no breaking changes were introduced.
5. **Database Check:** Ensure all database migrations have been successfully applied before allowing deployment.
6. **Server Config:** Ensure the `uvicorn` startup command and port configurations are correct for production.

## Instructions
- Run the skill by asking to "Run the pre-deploy-check skill".
- Output a strict pass/fail status and list any files that need modification before deployment.
