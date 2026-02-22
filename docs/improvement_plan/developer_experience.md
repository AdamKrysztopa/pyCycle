# Improvement Plan: Developer Experience

**Related audit**: [Maintainability Risk](../audit/07_risk_maintainability.md), [Code Quality Findings](../audit/08_code_quality_findings.md)  
**Related PRs**: PR 10 — Documentation & Refactoring

---

## DX-01: Type Hints and Static Typing Baseline

**Current state**: No type hints in the `pycycle/` package. `mypy` exists in dev dependencies but is unused.

**Improvement**:
1. Add type hints to core modules first: `mp_cycle.py`, `element_base.py`, `flow_in.py`, `connect_flow.py`, `api.py`
2. Define minimal protocol/alias types for OpenMDAO objects (e.g., `ProblemLike`, `GroupLike`)
3. Add `py.typed` marker for downstream type checkers

**Files to modify**:
- [`pycycle/mp_cycle.py`](../../pycycle/mp_cycle.py)
- [`pycycle/element_base.py`](../../pycycle/element_base.py)
- [`pycycle/flow_in.py`](../../pycycle/flow_in.py)
- [`pycycle/connect_flow.py`](../../pycycle/connect_flow.py)
- [`pycycle/api.py`](../../pycycle/api.py)
- [`pyproject.toml`](../../pyproject.toml) — mypy config

**Files to create**: `pycycle/py.typed`  
**Depends on**: None  
**Risk**: LOW — additive hints only

---

## DX-02: Logging and Error Messages

**Current state**: Error handling is inconsistent; some errors are thrown with no actionable context. Example: [`mp_cycle.py`](../../pycycle/mp_cycle.py:197) raises a `ValueError` for multiple design points with a generic message.

**Improvement**:
- Create a dedicated `pycycle/errors.py` with custom exception types:
  - `CycleConfigurationError`
  - `FlowConnectionError`
  - `MapConfigurationError`
- Ensure all raises include subsystem name, flow port, and the expected/actual values

**Files to modify**:
- [`pycycle/mp_cycle.py`](../../pycycle/mp_cycle.py)
- [`pycycle/element_base.py`](../../pycycle/element_base.py)
- [`pycycle/connect_flow.py`](../../pycycle/connect_flow.py)

**Files to create**: `pycycle/errors.py`  
**Depends on**: None  
**Risk**: LOW

---

## DX-03: Formatting, Linting, and Pre-commit

**Current state**: `black`, `flake8`, `isort` exist as dev deps but not enforced. No pre-commit hooks.

**Improvement**:
1. Add `.pre-commit-config.yaml` with `black`, `flake8`, `isort`, `ruff`
2. Add `make lint` and `make format` commands
3. Update CI to run lint steps (see TST-07)

**Files to create**: `.pre-commit-config.yaml`  
**Files to modify**: `pyproject.toml`, `.github/workflows/pycycle_test_workflow.yml`  
**Depends on**: None  
**Risk**: LOW

---

## DX-04: Development Scripts

**Current state**: No helper scripts for common tasks.

**Improvement**: Add a `Makefile` at repo root with targets:

- `make test`
- `make lint`
- `make format`
- `make docs`
- `make coverage`

**Files to create**: `Makefile`  
**Depends on**: DX-03  
**Risk**: LOW

---

## DX-05: Regression Data Management

**Current state**: Regression data is stored in `pycycle/elements/test/reg_data/` but not documented. No clear workflow for updating.

**Improvement**: Add a `docs/REGRESSION_DATA.md` describing:

- How regression data is generated
- Expected precision tolerances
- How to update data when physics changes

**Files to create**: `docs/REGRESSION_DATA.md`  
**Depends on**: None  
**Risk**: LOW

---

## DX-06: Code Ownership and Review Process

**Current state**: No CODEOWNERS file. PR review requirements are not documented.

**Improvement**:
1. Add `.github/CODEOWNERS`
2. Document review requirements in `CONTRIBUTING.md`

**Files to create**: `.github/CODEOWNERS`  
**Depends on**: DOC-05  
**Risk**: LOW

---

## DX-07: Performance Debugging Hooks

**Current state**: No standard profiling or debugging hooks.

**Improvement**:
- Add optional OpenMDAO solver tracing config that can be enabled via env var
- Provide a helper function in `pycycle/viewers.py` to print solver iteration summary

**Files to modify**:
- [`pycycle/viewers.py`](../../pycycle/viewers.py)  
**Depends on**: SOL-05 (solver iteration stats)  
**Risk**: LOW

---

## Summary

| ID | Improvement | Priority | Risk | Phase |
|----|------------|----------|------|-------|
| DX-01 | Type hints baseline | MEDIUM | LOW | 2 |
| DX-02 | Error messages + custom exceptions | MEDIUM | LOW | 1 |
| DX-03 | Formatting + pre-commit | HIGH | LOW | 1 |
| DX-04 | Development Makefile | MEDIUM | LOW | 1 |
| DX-05 | Regression data guide | LOW | LOW | 2 |
| DX-06 | CODEOWNERS and review process | LOW | LOW | 2 |
| DX-07 | Performance debug hooks | LOW | LOW | 3 |
