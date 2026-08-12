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
