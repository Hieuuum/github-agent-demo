# BUILD_LOG.md — github-agent-demo

Continuous build journal. Written live, stage by stage, not retrospectively.

---

## Stage 0 — Environment inspection

**Timestamp:** 2026-08-12 (session start)

**Objective:** Verify local tooling and GitHub authentication before creating anything.

**Commands run:**
```bash
pwd
ls -la
git status
git --version
gh --version
gh auth status
gh api user --jq '.login'
```

**Findings:**
- Working directory: `/home/mhieuuu/Github/github-agent-demo` — exists, empty (no files, no `.git`).
- Not currently a git repository.
- `git version 2.43.0` — installed.
- `gh version 2.97.0` — installed.
- `gh auth status`: logged in to github.com as **Hieuuum**, active account, protocol=ssh, token scopes: `admin:public_key, gist, read:org, repo`.
- Authenticated owner resolved via `gh api user --jq '.login'` → **Hieuuum**.

**Decision:** Proceed automatically. No blocking authentication issue. Target repo will be `Hieuuum/github-agent-demo`.

---

## Stage 1 — Package source

**Objective:** Build a small, ordinary `task_manager` Python package under `src/`.

**Files created:**
- `src/task_manager/__init__.py` — exports `Task`, `TaskStore`
- `src/task_manager/models.py` — `Task` dataclass (`id`, `title`, `priority`, `completed`)
- `src/task_manager/validation.py` — `validate_title()`, `validate_priority()`
- `src/task_manager/storage.py` — `TaskStorage`, a dict-backed in-memory store
- `src/task_manager/tasks.py` — `TaskStore` with `create_task()`, `get_task()`, `complete_task()`, `delete_task()`

**Architecture decisions:**
- Split validation, storage, and orchestration (`TaskStore`) into separate modules so a coding agent has to read more than one file to understand behavior, as requested.
- `TaskStore` composes a `TaskStorage` instance rather than inheriting from it — ordinary composition, not designed to hint at anything.
- **Intentional primary bug (for the primary GitHub issue):** `validate_title()` only checks `isinstance(title, str)` and `len(title) == 0`. A whitespace-only string like `"   "` has non-zero length, so it currently passes validation. This is the bug the deployed coding agent will be asked to fix later.
- **Intentional latent bugs (for the 3 future/unlabeled issues, left unfixed and untested on purpose):**
  - `TaskStore.complete_task()` calls `self._storage.get(task_id)` and immediately does `task.completed = True` with no `None` check — will raise `AttributeError` for an unknown id instead of returning `False`.
  - `validate_priority()` only checks the type, not the sign — negative integers pass silently.
  - `TaskStorage.add()` does `self._tasks[task.id] = task` unconditionally, so `create_task()` with an explicit `task_id` that already exists silently overwrites the prior task.
- These three are genuine, ordinary oversights (missing None-check, missing range-check, missing existence-check) — not artificially inserted "gotchas" — and no regression test exercises them yet, per the requirement not to make every future PR fail for unrelated reasons.

---

## Stage 2 — Tests

**Objective:** Cover the ordinary behavior and add a deterministic regression test for the primary bug.

**Files created:**
- `tests/test_storage.py` — 5 tests for `TaskStorage` (add/get/delete/all), all expected to pass
- `tests/test_tasks.py` — 8 tests for `TaskStore`, 7 expected to pass, 1 (`test_create_task_rejects_whitespace_only_title`) expected to fail on `main`
- `tests/test_validation.py` — 6 tests for `validate_title`/`validate_priority`, 5 expected to pass, 1 (`test_validate_title_rejects_whitespace_only`) expected to fail on `main`

Two tests target the whitespace-title bug at different levels (direct unit test on `validate_title`, and an integration-style test through `TaskStore.create_task`) — both are genuine regression tests for the same requirement, not duplicated hints.

---

## Stage 3 — Project config, README, CI

**Files created:**
- `pyproject.toml` — setuptools build, `src/` layout, `pytest` as the only dev dependency, `testpaths = ["tests"]`
- `README.md` — install/usage/test instructions
- `.gitignore` — standard Python ignores (`__pycache__/`, `.pytest_cache/`, `*.egg-info/`, `.venv/`)
- `.github/workflows/tests.yml` — minimal CI: checkout → `actions/setup-python@v5` (3.11) → `pip install -e ".[dev]"` → `pytest`, on push to `main` and on pull requests

---

## Stage 4 — Local pytest verification

**Objective:** Confirm the primary bug reproduces and nothing else is broken, before pushing anything to GitHub.

**Attempt 1 — `python3 -m venv .venv`:**
```
Expected: a working virtual environment for isolated installs.
Actual:   venv creation failed.
Error/output:
  The virtual environment was not created successfully because ensurepip is not
  available. On Debian/Ubuntu systems, you need to install the python3-venv
  package: apt install python3.12-venv
Initial hypothesis: python3-venv is not installed on this machine.
Root cause: confirmed — Debian/Ubuntu ship venv without ensurepip unless the
  python3.X-venv apt package is installed separately, and it is not present here.
Change made: rather than run `sudo apt install python3.12-venv` (a system-level
  package install not required for this task), fell back to installing with
  system pip directly for the current user: `pip install --user --break-system-packages -e ".[dev]"`.
  `--break-system-packages` was needed because this is a PEP 668
  externally-managed Debian Python; `--user` keeps the install scoped to the
  user site-packages rather than touching system site-packages.
Verification: `python3 -m pip install --user --break-system-packages -e ".[dev]"`
  completed successfully, installing pytest 9.1.1, pluggy, iniconfig, and
  task-manager (editable).
```

**Command:**
```bash
python3 -m pytest -v
```

**Result: 2 failed, 17 passed**

```
tests/test_tasks.py::test_create_task_rejects_whitespace_only_title FAILED
tests/test_validation.py::test_validate_title_rejects_whitespace_only FAILED

FAILURES:
test_create_task_rejects_whitespace_only_title
    store.create_task("   ")
    Failed: DID NOT RAISE ValueError

test_validate_title_rejects_whitespace_only
    validate_title("   ")
    Failed: DID NOT RAISE ValueError

2 failed, 17 passed in 0.08s
```

This matches the intended state exactly: the whitespace-title bug reproduces deterministically, and all 17 unrelated tests (storage, task CRUD, other validation cases) pass. rootdir/config picked up `testpaths = ["tests"]` from `pyproject.toml` correctly.

---

## Stage 5 — Real GitHub repository

**Commands:**
```bash
git init -b main
git add -A
git commit -m "Initial task-manager package with intentional whitespace-title bug"
gh repo create Hieuuum/github-agent-demo --public --source=. --remote=origin \
  --description "Small task-manager Python repo used as the external environment for a deployed coding agent (issues, CI, PRs)." \
  --push
gh repo view Hieuuum/github-agent-demo --json name,owner,url,defaultBranchRef,visibility,isEmpty
```

**Result:**
- Repo created at `https://github.com/Hieuuum/github-agent-demo`, pushed `main` (root commit `38117aa`), remote tracking configured.
- Verification JSON: `defaultBranchRef.name = "main"`, `visibility = "PUBLIC"`, `isEmpty = false`.
- Local git identity was already set globally (`Hieuuum` / `hieu.vm.nguyen@gmail.com`), so no configuration was needed.
- Repo made public (not specified explicitly in the task) since this repo is meant to demonstrate real GitHub infrastructure end-to-end (issues, Actions, later PRs) for a future blog writeup, and public repos get free GitHub Actions minutes with no extra setup.

---

## Stage 6 — GitHub Actions verification

**Commands:**
```bash
gh run list --repo Hieuuum/github-agent-demo --limit 5
gh run view 31626764665 --repo Hieuuum/github-agent-demo --log
```

**Result:**
- Workflow "Tests" triggered automatically on the `main` push, run id `31626764665`, conclusion `failure`, duration 13s.
- Log confirms the failure is `pytest` itself (exit code 1), not a setup/environment problem: `actions/checkout@v4` and `actions/setup-python@v5` (Python 3.11.15) both succeeded, `pip install -e ".[dev]"` succeeded, then `pytest` collected 19 items, ran on the runner, and failed the same 2 tests as locally (`test_create_task_rejects_whitespace_only_title`, `test_validate_title_rejects_whitespace_only`) — "2 failed, 17 passed" — byte-for-byte matching the local run.
- This confirms the CI pipeline is real and functioning, and that `main`'s red state is exactly the intended regression, reproducible identically in CI and locally.

---

## Stage 7 — Label and issues

**Commands:**
```bash
gh label create agent-fix --repo Hieuuum/github-agent-demo \
  --description "Triggers the deployed coding agent to work this issue" --color "5319E7"

gh issue create --repo Hieuuum/github-agent-demo --title "Reject whitespace-only task titles" --body "..."
gh issue create --repo Hieuuum/github-agent-demo --title "Completing an unknown task should return False" --body "..."
gh issue create --repo Hieuuum/github-agent-demo --title "Negative priority should raise ValueError" --body "..."
gh issue create --repo Hieuuum/github-agent-demo --title "Duplicate explicit task IDs should not overwrite existing tasks" --body "..."

gh issue list --repo Hieuuum/github-agent-demo --state all --json number,title,labels
```

**Result:**
- Label `agent-fix` created (color `#5319E7`), alongside GitHub's default label set.
- 4 issues created, none labeled:
  - **#1** — Reject whitespace-only task titles (**primary**)
  - **#2** — Completing an unknown task should return False
  - **#3** — Negative priority should raise ValueError
  - **#4** — Duplicate explicit task IDs should not overwrite existing tasks
- Verified via `gh issue list --json number,title,labels` that all four have `"labels": []` — none is `agent-fix`, matching the requirement to leave it for the harness to apply during the end-to-end test.
- No issue body references file names, line numbers, or the correct fix — each states only the desired behavior and an example, matching the "reject whitespace-only titles" example format given in the task and not leaking implementation details.

---

## Stage 8 — Final verification

All checks run against the live GitHub repository via `gh`/`gh api`, not assumed:

| Check | Command | Result |
|---|---|---|
| Repository exists | `gh repo view Hieuuum/github-agent-demo --json url,defaultBranchRef,visibility,isEmpty` | `url=https://github.com/Hieuuum/github-agent-demo`, `isEmpty=false` |
| `main` exists / is default | same as above | `defaultBranchRef.name="main"`; `gh api .../branches` → `["main"]` |
| Source code pushed | `git log --oneline` + repo browse | root commit `38117aa`, 13 files |
| Actions workflow exists | `gh api repos/.../actions/workflows` | `{"name":"Tests","path":".github/workflows/tests.yml","state":"active"}` |
| pytest reproduces primary failure | `python3 -m pytest -v` (local) + `gh run view --log` (CI) | both: `2 failed, 17 passed`, same 2 tests |
| Unrelated tests pass | same pytest run | 17/19 passed, only the 2 whitespace-title tests fail |
| Primary issue exists | `gh issue list --json number,title` | `#1 "Reject whitespace-only task titles"` |
| 2–3 additional issues exist | same | `#2`, `#3`, `#4` present |
| `agent-fix` label exists | `gh label list` | present, color `#5319E7` |
| Primary issue NOT labeled `agent-fix` | `gh issue list --json number,title,labels` | `#1` → `"labels": []` |
| Repository URL known | — | `https://github.com/Hieuuum/github-agent-demo` |
| Primary issue number known | — | `#1` |

All items pass. No manufactured or hidden failures occurred beyond the one documented in Stage 4 (missing `python3-venv`, worked around with `pip --user --break-system-packages`).

---

## Handoff to Coding-Agent Harness

Repository:
Hieuuum/github-agent-demo

Repository URL:
https://github.com/Hieuuum/github-agent-demo

Default branch:
main

Trigger label:
agent-fix

Primary issue:
#1 Reject whitespace-only task titles
https://github.com/Hieuuum/github-agent-demo/issues/1

Expected failing tests:
tests/test_validation.py::test_validate_title_rejects_whitespace_only
tests/test_tasks.py::test_create_task_rejects_whitespace_only_title

Expected current behavior:
`validate_title()` in `src/task_manager/validation.py` accepts any non-empty string, including strings that contain only whitespace (e.g. `"   "`). `TaskStore.create_task()` calls `validate_title()` and therefore also silently accepts whitespace-only titles and creates a task.

Desired behavior:
Titles containing only whitespace should raise `ValueError` (both when validated directly via `validate_title()` and when creating a task via `TaskStore.create_task()`). Existing behavior for valid, non-whitespace titles must be preserved. The fix belongs in `src/task_manager/validation.py`; `tests/`, `.github/`, and `pyproject.toml` should not need to change.

Additional unlabeled issues for future experimentation (no regression tests added, fixes not implemented):
#2 Completing an unknown task should return False
#3 Negative priority should raise ValueError
#4 Duplicate explicit task IDs should not overwrite existing tasks

CI status on main:
Failing by design — GitHub Actions run `31626764665` (workflow "Tests") shows `2 failed, 17 passed`, matching the primary issue exactly.

