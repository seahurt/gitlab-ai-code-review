# Plan: GitLab Auto Code Review Tool (CLI Based - User Centric)

## Objective
Create a tool that identifies the current authenticated GitLab user, finds all open Merge Requests where they are listed as a **Reviewer**, downloads the diffs, reviews them with a local `codex` CLI, and posts the results.

## Architecture
- **Language:** Python
- **Dependencies:** `python-gitlab`, `python-dotenv`.
- **External Tool:** `codex` (CLI).

## Steps

1. **GitLab Integration Module Updates**
    - [x] Add `get_current_user()` to identify the logged-in user.
    - [x] Add `get_pending_reviews()` to fetch MRs with `scope='all'`, `state='opened'`, and `reviewer_id=<current_user_id>`.

2. **Core Logic (Review Engine) Updates**
    - [x] Update `Reviewer.run()`:
        -   If no specific MR provided:
            -   Fetch current user info.
            -   Fetch all pending reviews for this user.
            -   Iterate and process each MR.

3. **CLI Interface Updates**
    - [x] Update `main.py`:
        -   Make `--project-id` and `--mr-iid` optional.
        -   Default behavior: Scan for all assigned reviews.

4. **Cleanup**
    - [x] Verify `requirements.txt` and `.env` match new needs.
