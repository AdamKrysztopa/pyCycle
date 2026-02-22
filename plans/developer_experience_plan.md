# Developer Experience Implementation Plan (DX-01..DX-07)

## Scope Confirmation
- Implement all DX items from [`docs/improvement_plan/developer_experience.md`](docs/improvement_plan/developer_experience.md:1).
- Treat DX-03 as already present but **verify and align** with uv-based workflow.
- Use `uv run` for all Makefile targets and dev tooling.
- Enable mypy strict mode where possible, with pragmatic opt-outs for third-party libs.

## Current State Summary
- Pre-commit exists with `black`, `isort`, `flake8` in [`.pre-commit-config.yaml`](.pre-commit-config.yaml:1).
- CI workflow uses conda/pip in [`.github/workflows/pycycle_test_workflow.yml`](.github/workflows/pycycle_test_workflow.yml:1).
- Mypy config is minimal in [`pyproject.toml`](pyproject.toml:101).
- Core modules for typing and error updates are:
  - [`pycycle/mp_cycle.py`](pycycle/mp_cycle.py:1)
  - [`pycycle/element_base.py`](pycycle/element_base.py:1)
  - [`pycycle/flow_in.py`](pycycle/flow_in.py:1)
  - [`pycycle/connect_flow.py`](pycycle/connect_flow.py:1)
  - [`pycycle/api.py`](pycycle/api.py:1)

---

## DX-01: Type Hints and Static Typing Baseline
**Goal:** Add minimal, low-risk type hints to core modules and enable mypy strict mode incrementally.

**Planned changes**
- Add type hints to public APIs and internal helpers in:
  - [`pycycle/mp_cycle.py`](pycycle/mp_cycle.py:1)
  - [`pycycle/element_base.py`](pycycle/element_base.py:1)
  - [`pycycle/flow_in.py`](pycycle/flow_in.py:1)
  - [`pycycle/connect_flow.py`](pycycle/connect_flow.py:1)
  - [`pycycle/api.py`](pycycle/api.py:1)
- Add lightweight OpenMDAO protocol/alias types in a new module (proposed):
  - `pycycle/typing.py` (new)
  - Example: `ProblemLike`, `GroupLike`, `SystemLike` protocols for `get_val`, `set_val`, `model`, `add_subsystem`.
- Add `pycycle/py.typed` marker for downstream typing support.
- Update mypy config in [`pyproject.toml`](pyproject.toml:101):
  - `strict = true`
  - Keep `ignore_missing_imports = true`
  - Add selective `per-module` ignores for OpenMDAO and matplotlib if needed.

**Notes**
- Strict typing will be applied to the new annotations only; any mypy blockers will be handled via `# type: ignore` in limited cases.

---

## DX-02: Logging and Error Messages
**Goal:** Introduce custom exceptions and consistent, actionable error messages.

**Planned changes**
- Create [`pycycle/errors.py`](pycycle/errors.py:1) with:
  - `CycleConfigurationError`
  - `FlowConnectionError`
  - `MapConfigurationError`
- Update raise sites with richer context:
  - [`pycycle/mp_cycle.py`](pycycle/mp_cycle.py:1)
    - `_setup_check` → `CycleConfigurationError` with class name and missing `super().setup()`.
    - Missing output port data → `FlowConnectionError` with `src_element`, `out_port`, `target_element`.
    - Design/off-design point config errors → `CycleConfigurationError` with expected/actual points.
    - Duplicate cycle param name → `CycleConfigurationError` with name.
    - Checkpoint state validation → `CycleConfigurationError` with required keys.
    - `solve_case_sequence` missing prob → `CycleConfigurationError` with guidance.
  - [`pycycle/element_base.py`](pycycle/element_base.py:1)
    - `copy_flow` invalid argument → `FlowConnectionError` with argument type/value.
  - [`pycycle/connect_flow.py`](pycycle/connect_flow.py:1)
    - Keep deprecation warning; no new exceptions added here.

---

## DX-03: Formatting, Linting, and Pre-commit (Verification)
**Goal:** Align pre-commit with uv-based commands and ensure parity with DX plan.

**Planned changes**
- Keep existing hooks, add `ruff` hook to [`.pre-commit-config.yaml`](.pre-commit-config.yaml:1) to match dev deps.
- Ensure lint/format commands are mirrored in Makefile (DX-04).
- Note: CI lint steps are part of TST-07; for now, just ensure local linting is consistent.

---

## DX-04: Development Scripts (Makefile)
**Goal:** Add uv-based Makefile targets for common tasks.

**Makefile targets**
- `make test` → `uv run testflo -n 1 pycycle --timeout=240 --show_skipped` (align with existing CI style)
- `make lint` → `uv run ruff check .` + `uv run flake8 .`
- `make format` → `uv run black .` + `uv run isort .`
- `make docs` → `uv run make -C pycycle/docs html`
- `make coverage` → `uv run testflo -n 1 pycycle --coverage --coverpkg pycycle --durations=20`

---

## DX-05: Regression Data Management Guide
**Goal:** Document workflow for regression data updates.

**Planned changes**
- Add [`docs/REGRESSION_DATA.md`](docs/REGRESSION_DATA.md:1) describing:
  - Location of regression data in `pycycle/elements/test/reg_data/`.
  - How to regenerate data (which tests/scripts, command patterns).
  - Tolerance expectations.
  - Process for updating when physics models change.

---

## DX-06: Code Ownership and Review Process
**Goal:** Introduce CODEOWNERS and document PR review expectations.

**Planned changes**
- Create [`.github/CODEOWNERS`](.github/CODEOWNERS:1) with owners for:
  - Core package (`pycycle/`)
  - Docs (`docs/`)
  - CI/workflows (`.github/`)
- Add or update [`CONTRIBUTING.md`](CONTRIBUTING.md:1) with review policy:
  - Required approvals
  - Expected CI checks
  - Doc update expectations for API changes

---

## DX-07: Performance Debugging Hooks
**Goal:** Provide opt-in solver tracing and summary output.

**Planned changes**
- Add an env-var controlled tracing option (proposed `PYCYCLE_SOLVER_TRACE=1`):
  - If enabled, configure OpenMDAO solver `iprint`, `debug_print`, or `print_bound_enforce` where supported.
- Add helper in [`pycycle/viewers.py`](pycycle/viewers.py:1) to print a solver iteration summary.
- Note dependency on SOL-05; implement a minimal summary now and expand later.

---

## Implementation Sequence
1. Add `pycycle/typing.py` and `pycycle/py.typed`.
2. Update [`pyproject.toml`](pyproject.toml:101) mypy settings for strict mode with targeted ignores.
3. Add type hints to the five core modules.
4. Add [`pycycle/errors.py`](pycycle/errors.py:1) and replace raise sites in `mp_cycle`, `element_base`.
5. Update [`.pre-commit-config.yaml`](.pre-commit-config.yaml:1) to include ruff hook.
6. Add root [`Makefile`](Makefile:1) using `uv run`.
7. Add [`docs/REGRESSION_DATA.md`](docs/REGRESSION_DATA.md:1).
8. Add [`.github/CODEOWNERS`](.github/CODEOWNERS:1) and update/create [`CONTRIBUTING.md`](CONTRIBUTING.md:1).
9. Add solver trace helpers in [`pycycle/viewers.py`](pycycle/viewers.py:1).

---

## Risks and Mitigations
- **Typing strictness noise**: limit strictness to new annotations, use per-module ignores for OpenMDAO.
- **Workflow drift**: Makefile commands mirror existing CI patterns to avoid divergence.
- **SOL-05 dependency**: DX-07 will provide minimal hooks now, expand later.

---

## Acceptance Checklist
- `uv run mypy` passes with strict mode and minimal ignores.
- `make lint` and `make format` succeed.
- `make test` and `make coverage` run with uv.
- New docs and governance files exist and are referenced in README or CONTRIBUTING as needed.
- New exceptions surface actionable context in error messages.
