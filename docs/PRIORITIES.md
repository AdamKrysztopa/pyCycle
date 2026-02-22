# pyCycle Improvement Priorities

This document consolidates all identified improvements from [`docs/audit/`](audit/) and [`docs/improvement_plan/`](improvement_plan/) into prioritized action categories.

---

## 🔴 MUST FIX NOW (Critical - Phase 1)

These issues pose immediate risks to correctness, stability, or maintainability. Address before adding new features.

### Correctness & Stability

| ID | Issue | Risk | Files | Status |
|----|-------|------|-------|--------|
| **TST-05** | Fix undefined [`AnalysisError`](../pycycle/elements/turbine.py:43) import | HIGH | [`turbine.py`](../pycycle/elements/turbine.py) | ✅ Done |
| **SOL-01** | Add continuation method for nozzle choke discontinuity | HIGH | [`nozzle.py`](../pycycle/elements/nozzle.py) | ✅ Done |
| **MAP-01** | Standardize map parameter names (Nc/Wc vs Np/Wp) | HIGH | All maps in [`pycycle/maps/`](../pycycle/maps/) | ✅ Done |

### Test Coverage Gaps

| ID | Issue | Risk | Files | Status |
|----|-------|------|-------|--------|
| **TST-01** | Add core module unit tests (mp_cycle, element_base, api) | HIGH | [`pycycle/tests/`](../pycycle/tests/) | ✅ Done |
| **TST-02** | Add map tests (currently zero) | HIGH | [`pycycle/maps/test/`](../pycycle/maps/test/) | ✅ Done |
| **TST-08** | Investigate "thermo weirdness" TODO in static tests | HIGH | [`test_thermo_total_static_*.py`](../pycycle/thermo/test/) | ⏳ Pending |

### Code Quality Basics

| ID | Issue | Risk | Files | Status |
|----|-------|------|-------|--------|
| **DX-03** | Add pre-commit hooks (black, flake8, isort) | HIGH | `.pre-commit-config.yaml` | ✅ Done |
| **TST-06** | Enable CI coverage reporting | MEDIUM | [`.github/workflows/`](../.github/workflows/) | ✅ Done |

### Example Runs (Phase 1 verification)

| Example | Command | Result | Notes |
|---------|---------|--------|-------|
| `simple_turbojet` | `uv run python example_cycles/simple_turbojet.py` | ✅ Completed | Runtime ~1.1s; RuntimeWarnings from `static_ps_resid` sqrt in console. |
| `single_spool_turboshaft` | `uv run python example_cycles/single_spool_turboshaft.py` | ✅ Completed | Runtime ~12.4s. |
| `high_bypass_turbofan` | `uv run python example_cycles/high_bypass_turbofan.py` | ✅ User-verified | User reports successful run in separate console; this run was stopped locally after repeated solver bound warnings. |

---

## 🟠 NEED TO FIX (High Priority - Phase 1-2)

These improvements significantly enhance usability, robustness, or developer experience.

### Solver Robustness

| ID | Issue | Priority | Files | Status |
|----|-------|----------|-------|--------|
| **SOL-02** | Add solver state checkpointing for restarts | HIGH | [`mp_cycle.py`](../pycycle/mp_cycle.py) | ✅ Done |
| **SOL-03** | Better initial guess heuristics | HIGH | [`compressor.py`](../pycycle/elements/compressor.py), [`turbine.py`](../pycycle/elements/turbine.py) | ✅ Done |
| **SOL-04** | Custom Newton linesearch callback | MEDIUM | [`element_base.py`](../pycycle/element_base.py) | ✅ Done |

### Architecture & API

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **S-01** | Simplify [`Cycle.pyc_connect_flow()`](../pycycle/mp_cycle.py:135) signature | HIGH | [`mp_cycle.py`](../pycycle/mp_cycle.py) |
| **S-02** | Deprecate `pyc_add_element()` and `pyc_add_pnt()` | HIGH | [`mp_cycle.py`](../pycycle/mp_cycle.py) |
| **S-03** | Extract flow graph traversal to `FlowGraph` class | MEDIUM | [`mp_cycle.py`](../pycycle/mp_cycle.py) |
| **S-08** | Split monolithic [`Compressor`](../pycycle/elements/compressor.py) class | MEDIUM | [`compressor.py`](../pycycle/elements/compressor.py) |

### Documentation

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **DOC-01** | Expand Sphinx API reference | HIGH | [`pycycle/docs/`](../pycycle/docs/) |
| **DOC-03** | Add usage cookbook | MEDIUM | `pycycle/docs/cookbook.rst` |
| **DOC-05** | Create CONTRIBUTING.md | MEDIUM | `CONTRIBUTING.md` |

### Developer Experience

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **DX-02** | Better error messages + custom exceptions | MEDIUM | `pycycle/errors.py` |
| **DX-04** | Add Makefile for common tasks | MEDIUM | `Makefile` |

---

## 🟡 SHOULD FIX (Medium Priority - Phase 2)

These improve quality of life and add valuable functionality but aren't blocking.

### Physics Models

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **PHY-01** | Add afterburner element | MEDIUM | `pycycle/elements/afterburner.py` |
| **PHY-04** | Add bleed reinjection element | MEDIUM | `pycycle/elements/bleed_reinject.py` |
| **PHY-05** | Integrate cooling with bleed | MEDIUM | [`cooling.py`](../pycycle/elements/cooling.py) |

### Map System

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **MAP-02** | Add map validation on load | MEDIUM | [`pycycle/maps/`](../pycycle/maps/) |
| **MAP-03** | Implement surge margin calculation | MEDIUM | [`compressor.py`](../pycycle/elements/compressor.py) |
| **MAP-05** | Add map scaling persistence | MEDIUM | [`mp_cycle.py`](../pycycle/mp_cycle.py) |

### Unit System

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **UNI-01** | Add `unit_system` option (ENG/SI) | MEDIUM | [`mp_cycle.py`](../pycycle/mp_cycle.py), [`element_base.py`](../pycycle/element_base.py) |
| **UNI-02** | Create unit mappings module | MEDIUM | `pycycle/unit_utils.py` |
| **UNI-03** | Replace `EngUnitProps` with generic `FlowUnitProps` | MEDIUM | [`unit_comps.py`](../pycycle/thermo/unit_comps.py) |

### Testing

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **TST-03** | Complete cooling test assertions | MEDIUM | [`test_cooling.py`](../pycycle/elements/test/test_cooling.py) |
| **TST-04** | Add negative tests (error paths) | MEDIUM | `pycycle/tests/test_errors.py` |
| **TST-07** | Add CI lint and type check steps | MEDIUM | [`.github/workflows/`](../.github/workflows/) |

### Documentation

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **DOC-02** | Expand tutorials (turbofan, turboshaft, etc.) | MEDIUM | [`pycycle/docs/tutorials/`](../pycycle/docs/tutorials/) |
| **DOC-04** | Flow station output reference | MEDIUM | `pycycle/docs/reference_guide/flow_station.rst` |

---

## 🟢 NICE TO HAVE (Low Priority - Phase 3)

These are refinements, optimizations, and polish items.

### Structure & Patterns

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **S-04** | Replace `DeprecatedDict` with proper warnings | LOW | [`constants.py`](../pycycle/constants.py) |
| **S-05** | Centralized cycle options registry | LOW | `pycycle/cycle_options.py` |
| **S-06** | Element lifecycle hooks (pre_setup, post_setup) | LOW | [`element_base.py`](../pycycle/element_base.py) |
| **S-09** | Factory pattern for element creation | LOW | `pycycle/element_factory.py` |
| **S-10** | Validation framework for cycle topology | LOW | `pycycle/validation.py` |

### Solver & Performance

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **SOL-05** | Add solver iteration stats viewer | LOW | [`viewers.py`](../pycycle/viewers.py) |
| **SOL-06** | Multi-point parallel solve strategy | LOW | [`mp_cycle.py`](../pycycle/mp_cycle.py) |
| **SOL-07** | Auto-tuning of Newton solver params | LOW | [`element_base.py`](../pycycle/element_base.py) |

### Physics

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **PHY-02** | Variable-area nozzle with actuation | LOW | [`nozzle.py`](../pycycle/elements/nozzle.py) |
| **PHY-03** | Variable-area inlet | LOW | [`inlet.py`](../pycycle/elements/inlet.py) |
| **PHY-06** | Turbine cooling with efficiency penalty | LOW | [`turbine.py`](../pycycle/elements/turbine.py) |
| **PHY-07** | Compressor bleed with performance loss | LOW | [`compressor.py`](../pycycle/elements/compressor.py) |
| **PHY-08** | Heat exchanger element | LOW | `pycycle/elements/heat_exchanger.py` |

### Maps

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **MAP-04** | Map extrapolation warnings | LOW | [`compressor_map.py`](../pycycle/elements/compressor_map.py) |
| **MAP-06** | Map fitting toolkit | LOW | `pycycle/maps/fitting.py` |

### Unit System

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **UNI-04** | Deprecate `g_c` usage | LOW | [`constants.py`](../pycycle/constants.py), [`nozzle.py`](../pycycle/elements/nozzle.py) |
| **UNI-05** | SI standard-day reference values | LOW | [`constants.py`](../pycycle/constants.py) |
| **UNI-06** | FlowIn unit awareness | MEDIUM | [`flow_in.py`](../pycycle/flow_in.py) |

### Testing

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **TST-09** | Performance benchmarks | LOW | `pycycle/tests/test_benchmarks.py` |

### Documentation

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **DOC-06** | Example gallery page | LOW | `pycycle/docs/examples/gallery.rst` |
| **DOC-07** | Document deprecation policy | LOW | [`release_notes.md`](../release_notes.md) |

### Developer Experience

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| **DX-01** | Add type hints to core modules | MEDIUM | Core `.py` files + `pycycle/py.typed` |
| **DX-05** | Regression data management guide | LOW | `docs/REGRESSION_DATA.md` |
| **DX-06** | CODEOWNERS and review process | LOW | `.github/CODEOWNERS` |
| **DX-07** | Performance debug hooks | LOW | [`viewers.py`](../pycycle/viewers.py) |

---

## Summary by Phase

### Phase 1 (Immediate — Correctness & Foundations)
**Total: 13 items**

Focus: Fix critical bugs, add missing tests, establish CI/CD basics, simplify API

- 3 correctness fixes (TST-05, SOL-01, MAP-01)
- 3 test coverage (TST-01, TST-02, TST-08)
- 2 CI/DX basics (DX-03, TST-06)
- 4 architecture (S-01, S-02, S-03, S-08)
- 1 documentation (DOC-01)

### Phase 2 (Enhancement — Robustness & Features)
**Total: 23 items**

Focus: Solver robustness, physics additions, unit system support, expanded docs

- 3 solver improvements (SOL-02, SOL-03, SOL-04)
- 3 physics models (PHY-01, PHY-04, PHY-05)
- 3 map enhancements (MAP-02, MAP-03, MAP-05)
- 3 unit system (UNI-01, UNI-02, UNI-03)
- 3 testing (TST-03, TST-04, TST-07)
- 4 documentation (DOC-02, DOC-03, DOC-04, DOC-05)
- 2 developer UX (DX-02, DX-04)
- 2 type hints/errors (DX-01 moved here, UNI-06)

### Phase 3 (Polish — Optimization & Refinement)
**Total: 25 items**

Focus: Advanced features, optimizations, comprehensive polish

- 6 structure refinements (S-04 through S-10, excluding S-08)
- 3 solver optimizations (SOL-05, SOL-06, SOL-07)
- 4 physics additions (PHY-02, PHY-03, PHY-06, PHY-07, PHY-08)
- 2 map tools (MAP-04, MAP-06)
- 3 unit system (UNI-04, UNI-05, UNI-06 if not done)
- 1 testing (TST-09)
- 2 documentation (DOC-06, DOC-07)
- 4 developer experience (DX-05, DX-06, DX-07, and type hints continuation)

---

## Cross-Reference

For detailed implementation plans, see:
- **Audit findings**: [`docs/audit/`](audit/)
- **Improvement details**: [`docs/improvement_plan/`](improvement_plan/)
- **PR roadmap**: [`docs/audit/09_pr_roadmap.md`](audit/09_pr_roadmap.md)
