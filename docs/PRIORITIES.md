# pyCycle Priorities (NPSS-Fidelity First)

This roadmap prioritizes one goal above all others: improve physical-model fidelity and matching behavior to NPSS-style cycle modeling.

## Priority Rule

When there is a tradeoff, choose work that improves:
1. Physical realism in core engine elements.
2. Agreement vs NPSS baselines/regression data.
3. Solver robustness across physically hard transitions.

Documentation, refactors, and developer ergonomics are important, but they follow fidelity-critical work.

## Current Baseline (Repo Review)

Already in place and should be preserved:
- Nozzle choke blending is now smoothed in [`pycycle/elements/nozzle.py`](../pycycle/elements/nozzle.py).
- `MPCycle.solve_case_sequence()` exists in [`pycycle/mp_cycle.py`](../pycycle/mp_cycle.py).
- Compressor stall-margin outputs (`SMN`, `SMW`) already exist in [`pycycle/elements/compressor_map.py`](../pycycle/elements/compressor_map.py).

Still major NPSS-parity gaps:
- No dedicated `Afterburner` element (examples use a second `Combustor`).
- No variable-geometry nozzle mode with commanded exit area input.
- Turbine cooling remains a separate workflow, not integrated into `Turbine`.
- No standard bleed reinjection element.

Status update (current branch work):
- `unit_system` plumbing (`ENG`/`SI`) has been added to `Cycle`/`Element` and propagated to element thermo/flow components.
- Flow output wrappers are now unit-system aware (`FlowUnitProps` / `FlowUnitStaticProps`) with compatibility aliases retained.
- Explicit `g_c` usage has been removed from inlet/nozzle performance equations.
- Runtime unit declarations were unified across nozzle/turbine/shaft/performance/map/ambient/flight/cooling/gearbox/CFD start and thermo-add interfaces.
- Additional runtime cleanup completed in `pycycle/elements/compressor.py` and `pycycle/elements/duct.py` (internal helper components).
- Example-cycle unit/guess handling was updated for robust ENG/SI execution across all primary examples (`electric_propulsor`, `wet_propulsor`, `simple_turbojet`, `wet_simple_turbojet`, `single_spool_turboshaft`, `multi_spool_turboshaft`, `mixedflow_turbofan`, `afterburning_turbojet`) plus bounded verification of `high_bypass_turbofan`.
- Validation status: full ENG/SI example sweep passes for the examples above; high-bypass runs stably through multiple schedule points in both ENG and SI (long sweep intentionally interrupted after stability confirmation); full element+thermo suite remains at the known baseline 4 failures in `test_nozzle_CV_CD.py`.

## Phase 0 (Immediate): NPSS Validation Harness

Before adding more features, lock down how fidelity is measured.

| ID | Item | Why now | Files |
|----|------|---------|-------|
| **VAL-01** | Define NPSS parity matrix (component + cycle cases) | Prevent subjective "close enough" decisions | `docs/REGRESSION_DATA.md`, `docs/RUNNING_EXAMPLES.md` |
| **VAL-02** | Add/refresh golden datasets for choke transition, cooled turbine, bleed mixing, AB on/off | Required to verify physics changes | `pycycle/elements/test/reg_data/`, `example_cycles/tests/` |
| **TST-08** | Resolve thermo static "weirdness" and codify expected behavior | Thermo mismatch can hide physics regressions | `pycycle/thermo/test/test_thermo_total_static_*.py` |

## Phase 1 (Highest): Core Physics for NPSS-Like Capability

These are the most important backlog items.

| ID | Item | Priority | Files |
|----|------|----------|-------|
| **PHY-01** | Implement dedicated `Afterburner` element (lightoff + reheat loss model) | CRITICAL | `pycycle/elements/afterburner.py`, `pycycle/elements/test/test_afterburner.py` |
| **PHY-03** | Add variable-geometry nozzle mode (`A_exit` commanded input) | CRITICAL | `pycycle/elements/nozzle.py` |
| **PHY-04** | Integrate cooling rows directly into `Turbine` | CRITICAL | `pycycle/elements/turbine.py`, `pycycle/elements/cooling.py` |
| **PHY-05** | Add `BleedReinject` element | HIGH | `pycycle/elements/bleed_reinject.py` |
| **UNI-01** | Add cycle/element `unit_system` option (`ENG`/`SI`) | DONE | `pycycle/mp_cycle.py`, `pycycle/element_base.py` |
| **UNI-03** | Replace `EngUnitProps` with unit-system-aware flow output component | DONE | `pycycle/thermo/unit_comps.py` |
| **UNI-04** | Deprecate/remove explicit `g_c` conversions where unit algebra should handle it | DONE | `pycycle/constants.py`, `pycycle/elements/nozzle.py`, `pycycle/elements/inlet.py` |
| **UNI-06** | Runtime component declaration unification (`get_unit` across runtime-critical modules) | DONE | `pycycle/elements/{nozzle,turbine,shaft,performance,compressor_map,turbine_map,flight_conditions,ambient,cooling,gearbox,cfd_start}.py`, `pycycle/thermo/{cea,tabular}/thermo_add.py` |
| **UNI-07** | Power/torque and map interface unit-convention unification | DONE | `pycycle/unit_utils.py`, `pycycle/elements/{shaft,turbine,compressor,compressor_map,turbine_map}.py` |
| **UNI-08** | Dual-system targeted regression coverage for migrated components | DONE | `pycycle/elements/test/`, `pycycle/thermo/test/` |
| **UNI-09** | Required example matrix certification in ENG/SI | DONE | `example_cycles/{electric_propulsor,wet_propulsor,simple_turbojet,wet_simple_turbojet,single_spool_turboshaft,multi_spool_turboshaft,mixedflow_turbofan,afterburning_turbojet,high_bypass_turbofan}.py` |

## Phase 2 (High): Maps + Solver Behavior for Robust Physical Runs

| ID | Item | Priority | Files |
|----|------|----------|-------|
| **MAP-02** | Map loader/validator for external (including NPSS-style) map ingestion | HIGH | `pycycle/map_utils.py`, `pycycle/maps/` |
| **MAP-04** | Extrapolation controls/warnings for map bounds | HIGH | `pycycle/elements/compressor_map.py`, `pycycle/elements/turbine_map.py` |
| **MAP-05** | Unify/document compressor vs turbine map scaling behavior | MEDIUM | `pycycle/elements/compressor_map.py`, `pycycle/elements/turbine_map.py` |
| **SOL-05** | Expand `guess_nonlinear` coverage where still weak | MEDIUM | `pycycle/elements/nozzle.py`, `pycycle/elements/mixer.py`, `pycycle/thermo/static_ps_resid.py` |
| **SOL-06** | Isolate thermo convergence internals to reduce solve fragility | MEDIUM | `pycycle/thermo/thermo.py` |
| **SOL-07** | Replace hardcoded tabular T/P bounds with dataset bounds | MEDIUM | `pycycle/thermo/thermo.py` |
| **TST-03** | Complete cooling assertions using validated reference values | MEDIUM | `pycycle/elements/test/test_cooling.py` |

## Phase 3 (After Fidelity Gaps Close): Architecture, Docs, DX

These are still valuable, but not on the critical path for NPSS-like physical modeling:
- Structure/API cleanups from [`docs/improvement_plan/structure.md`](improvement_plan/structure.md)
- Documentation expansion from [`docs/improvement_plan/documentation.md`](improvement_plan/documentation.md)
- Developer experience improvements from [`docs/improvement_plan/developer_experience.md`](improvement_plan/developer_experience.md)

## Exit Criteria for "NPSS-Comparable" Milestone

1. NPSS parity matrix exists and is automated in tests.
2. Afterburner + variable geometry nozzle + cooling-integrated turbine + bleed reinjection are implemented.
3. Unit system behavior is explicit and consistent across core flow variables.
4. Example cycles pass with bounded solver behavior across operating sweeps.

## Cross-Reference

For detailed implementation plans, see:
- **Audit findings**: [`docs/audit/`](audit/)
- **Improvement details**: [`docs/improvement_plan/`](improvement_plan/)
- **PR roadmap**: [`docs/audit/09_pr_roadmap.md`](audit/09_pr_roadmap.md)
