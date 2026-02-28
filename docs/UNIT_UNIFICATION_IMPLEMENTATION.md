# Unit Unification Implementation

This document is the execution reference for full ENG/SI unification across pyCycle.
It combines:
- target architecture,
- current implementation status,
- remaining gaps,
- concrete code-change plan,
- validation and rollout strategy.

Last updated: 2026-02-23

## 1. Objective

Deliver a single cycle-wide `unit_system` (`ENG` or `SI`) that produces physically equivalent results with different unit labels/scales, without manual per-element edits.

Definition of done:
1. A user can set `Cycle(unit_system='SI')` and run all supported cycles.
2. ENG remains default and backward compatible.
3. No runtime element behavior depends on implicit English-only constants or assumptions.
4. Regression tests verify ENG/SI equivalence.

## 2. Design Principles

1. Thermo internals remain canonical.
- Keep internal thermo solves unchanged where possible; rely on OpenMDAO unit conversion at boundaries.

2. Boundary unit declarations are explicit and centralized.
- All user-facing IO declarations use `get_unit(...)`.

3. Unit conversions in equations are explicit where dimensions differ.
- Use conversion factors keyed by unit system (for example mass-flow x velocity to force).

4. Migration is incremental and non-breaking.
- ENG default behavior preserved.
- Keep deprecated aliases for one release cycle.

## 3. Canonical Architecture

## 3.1 Unit registry

Implemented in `pycycle/unit_utils.py`:
- `UNIT_SYSTEMS`
- `STD_DAY`
- `MASS_FLOW_VEL_TO_FORCE`
- `get_unit(var_type, unit_system)`

Expected use:
- Never hardcode `'degR'`, `'psi'`, `'lbm/s'`, `'Btu/lbm'`, `'hp'`, etc. in runtime code when the variable is user-facing.
- Always request unit strings via `get_unit`.

## 3.2 Option propagation

Implemented:
- `pycycle/mp_cycle.py`: `Cycle` declares and propagates `unit_system`.
- `pycycle/element_base.py`: `Element` declares `unit_system`.

Contract:
- Every element/subcomponent that declares external IO must be initialized with `unit_system=self.options['unit_system']`.

## 3.3 Thermo flow wrappers

Implemented:
- `pycycle/thermo/unit_comps.py`:
  - `FlowUnitProps`
  - `FlowUnitStaticProps`
  - compatibility aliases (`EngUnitProps`, `EngUnitStaticProps`)
- `pycycle/thermo/thermo.py` instantiates unit-aware wrappers.

## 3.4 Flow interfaces

Implemented:
- `pycycle/flow_in.py` is unit-aware and driven by `get_unit`.

## 3.5 Equation-level conversions

Implemented:
- Inlet/nozzle performance no longer use explicit `g_c`.
- Force conversion handled with `MASS_FLOW_VEL_TO_FORCE[unit_system]`.

Partially implemented:
- Other components still have ENG-specific power/torque or map-flow assumptions.

## 4. Current Status Snapshot

## 4.1 Completed

1. Core framework plumbing
- `Cycle` / `Element` `unit_system` option.
- Cycle option propagation includes `unit_system`.

2. Thermo-flow output wrappers
- Unit-aware flow output components in place.

3. Flow station input ports
- `FlowIn` now unit-aware.

4. Inlet and nozzle force equations
- Explicit `g_c` removed from compute path.

5. Compressor corrected-flow references
- `CorrectedInputsCalc` uses `STD_DAY` by unit system.

6. Example CLI support
- `--unit-system` added across example cycle scripts.

7. Dual-unit matrix runner/report
- `example_cycles/run_units_matrix.py`
- `docs/units_examples_report.md`

8. Critical derivative/runtime fix
- `pycycle/thermo/tabular/thermo_add.py` updated to support complex-step without float-cast failures.

## 4.2 Runtime-critical closure status

Completed in this implementation pass:

1. Runtime unit-declaration unification completed in:
- `pycycle/elements/nozzle.py` (`PR_bal`, `PressureCalcs`, `Mux`)
- `pycycle/elements/turbine.py`
- `pycycle/elements/shaft.py`
- `pycycle/elements/performance.py`
- `pycycle/elements/compressor_map.py`
- `pycycle/elements/turbine_map.py`
- `pycycle/elements/flight_conditions.py`
- `pycycle/elements/ambient.py`
- `pycycle/elements/cooling.py`
- `pycycle/elements/gearbox.py`
- `pycycle/elements/cfd_start.py`
- `pycycle/thermo/cea/thermo_add.py`
- `pycycle/thermo/tabular/thermo_add.py`

2. Additional runtime cleanup completed (beyond original runtime-critical list):
- `pycycle/elements/compressor.py`
- `pycycle/elements/duct.py`

3. Equation-level unit consistency improvements completed:
- Added system-indexed conversion constants in `pycycle/unit_utils.py` for enthalpy-flow to power and power/rpm to torque.
- Updated shaft/compressor/turbine helper calculations to use unit-system-indexed conversions.

4. Validation summary:
- Full example sweep run in both ENG and SI:
  - `example_cycles/electric_propulsor.py`
  - `example_cycles/wet_propulsor.py`
  - `example_cycles/simple_turbojet.py`
  - `example_cycles/wet_simple_turbojet.py`
  - `example_cycles/single_spool_turboshaft.py`
  - `example_cycles/multi_spool_turboshaft.py`
  - `example_cycles/mixedflow_turbofan.py`
  - `example_cycles/afterburning_turbojet.py`
- Long schedule bounded validation in both ENG and SI:
  - `example_cycles/high_bypass_turbofan.py` (confirmed stable progression through multiple operating points; run intentionally interrupted before full sweep completion)
- Full `pycycle/elements/test` + `pycycle/thermo/test` remains at known baseline failures:
  - 4 failures in `pycycle/elements/test/test_nozzle_CV_CD.py` (existing nozzle MN tolerance mismatch).

## 4.3 Non-blocking (documentation/tests/examples)

Many tests/docs still reference ENG units intentionally or by default. They should be updated, but these are not blockers for core runtime unification if runtime APIs are unit-system-safe.

## 4.4 Bleed semantics (must be explicit in unit docs)

pyCycle bleed controls are mostly **unitless fractions**, and this must be stated explicitly because it affects interpretation and calibration.

Current behavior in runtime code:

1. Standalone bleed extraction (`BleedOut`)
- file: `pycycle/elements/bleed_out.py`
- input: `{bleed_name}:frac_W`
- definition: `W_bleed / W_in` at that bleed element inlet.
- equation: `W_bleed = W_in * frac_W`, `W_out = W_in - sum(W_bleed_i)`.

2. Compressor interstage/customer bleeds (`BleedsAndPower`)
- file: `pycycle/elements/compressor.py`
- `frac_W`: mass-flow fraction relative to local compressor inlet flow (`W_bleed / W_in`).
- `frac_P`: pressure interpolation fraction between compressor inlet and outlet total pressure:
  `Pt_bleed = Pt_in + frac_P * (Pt_out - Pt_in)`.
- `frac_work`: enthalpy/work interpolation fraction between compressor inlet and outlet enthalpy:
  `ht_bleed = ht_in + frac_work * (ht_out - ht_in)`.

3. Turbine bleed re-entry pressure placement (`BleedPressure`)
- file: `pycycle/elements/turbine.py`
- `frac_P` is the interpolation fraction across turbine pressure drop where bleed flow is introduced:
  `Pt_bleed = Pt_out + frac_P * (Pt_in - Pt_out)`.
- Turbine bleed mass flow `BN:W` is taken from connected bleed streams, not defined as a direct fraction inside `BleedPressure`.

Important interpretation:
1. These are not globally normalized to "core flow at engine face" unless you enforce that relation externally.
2. In multi-spool models, chained bleeds are local to the station where they are applied.
3. Unit-system migration does not change bleed fraction semantics because `frac_*` values are dimensionless.

Documentation requirement:
1. `QUICK_REFERENCE.md` and `RUNNING_EXAMPLES.md` should define these bleed fractions explicitly.
2. Example comments should state the reference flow for each `frac_W` assignment.

## 5. Implementation Plan (Remaining Work)

## 5.1 Phase A: Runtime IO declaration unification

Goal: remove ENG-hardcoded declarations from runtime components.

Tasks:
1. In each remaining runtime component:
- add `unit_system` option if missing.
- replace unit literals with `get_unit(...)`.

2. Affected files:
- `pycycle/elements/nozzle.py` (remaining subcomponents)
- `pycycle/elements/turbine.py`
- `pycycle/elements/shaft.py`
- `pycycle/elements/performance.py`
- `pycycle/elements/compressor_map.py`
- `pycycle/elements/turbine_map.py`
- `pycycle/elements/flight_conditions.py`
- `pycycle/elements/ambient.py`
- `pycycle/elements/cooling.py`
- `pycycle/elements/gearbox.py`
- `pycycle/elements/cfd_start.py`
- `pycycle/thermo/cea/thermo_add.py`
- `pycycle/thermo/tabular/thermo_add.py`

3. Acceptance:
- no hardcoded ENG unit literals in runtime component declarations except where explicitly documented as ENG-only legacy behavior.

## 5.2 Phase B: Equation consistency and map/power conventions

Goal: ensure formula behavior is invariant across unit systems.

Tasks:
1. Audit equations that include implicit ENG conversion constants.
2. For each such equation:
- express in unit-consistent form,
- or use system-indexed conversion constants from `unit_utils.py`.
3. Revisit power/torque conversion assumptions in:
- `pycycle/elements/shaft.py`
- `pycycle/elements/turbine.py`
- `pycycle/elements/performance.py`

4. Map conventions:
- decide canonical corrected/referred flow units and convert at boundaries.
- ensure compressor/turbine map APIs are symmetric in unit treatment.

5. Acceptance:
- check_partials in ENG and SI passes for updated components.

## 5.3 Phase C: Viewer/report/documentation closure

Goal: ensure user-visible outputs are coherent in both unit systems.

Tasks:
1. Extend viewer helpers that still print ENG-only labels.
2. Update quick-reference/run docs to present ENG and SI examples side-by-side.
3. Make report generation robust across all selected example cycles.

4. Acceptance:
- user can run examples with `--unit-system SI` and output tables/labels are SI-consistent.

## 5.4 Phase D: Test closure and CI gating

Goal: prevent regressions.

Tasks:
1. Expand unit regression test set beyond mini-cycle:
- inlet, nozzle, compressor, turbine, shaft/performance, map interfaces.

2. Add dual-system checks:
- run same case in ENG and SI,
- compare physically equivalent outputs after conversion.

3. Add example smoke matrix:
- at minimum run and verify convergence for:
  - `example_cycles/electric_propulsor.py`
  - `example_cycles/simple_turbojet.py`
  - `example_cycles/multi_spool_turboshaft.py`

4. Acceptance:
- CI includes unit-system regression jobs.

## 6. Detailed File-Level Migration Guide

## 6.1 Nozzle (`pycycle/elements/nozzle.py`)

Remaining issue:
- Subcomponents still use ENG literals for pressure/entropy/enthalpy/density/velocity/area.

Required changes:
1. Add `unit_system` options to `PR_bal`, `PressureCalcs`, `Mux`.
2. Replace all IO `units='...'` with `get_unit(...)`.
3. Keep dimensional consistency of pressure-area term and flow terms.
4. Verify `check_partials` in ENG and SI.

## 6.2 Turbine (`pycycle/elements/turbine.py`)

Remaining issue:
- Large number of internal subcomponents still hardcoded to ENG units.

Required changes:
1. Add or propagate `unit_system` in all turbine helper components.
2. Replace all unit declarations with `get_unit`.
3. Verify shaft-power and torque outputs remain physically identical between systems.
4. Re-run turbine unit tests and off-design tests in both systems.

## 6.3 Shaft/Performance (`pycycle/elements/shaft.py`, `pycycle/elements/performance.py`)

Remaining issue:
- ENG-only units and conversion assumptions for power and torque.

Required changes:
1. Add `unit_system` option.
2. Use `get_unit('power', unit_system)` and `get_unit('torque', unit_system)`.
3. Ensure all internal conversion constants are system-aware.
4. Add dual-system derivative and value-parity tests.

## 6.4 Maps (`pycycle/elements/compressor_map.py`, `pycycle/elements/turbine_map.py`)

Remaining issue:
- Corrected/referred flow units hardcoded as `lbm/s`.

Required changes:
1. Convert map-facing IO declarations to unit-system-aware mass-flow units.
2. Keep map normalization dimensionless and invariant.
3. Validate map interpolation outputs match after conversion.

## 6.5 FlightConditions/Ambient/CFDStart

Remaining issue:
- Hardcoded ENG balance/input units.

Required changes:
1. `FlightConditions`: `Tt`/`Pt` balance units from `get_unit`.
2. `Ambient`: temperature units from `get_unit`.
3. `CFDStart`: replace ENG literals in balance definitions.

## 6.6 ThermoAdd interfaces (`pycycle/thermo/cea/thermo_add.py`, `pycycle/thermo/tabular/thermo_add.py`)

Remaining issue:
- Interface ports remain ENG unit declarations.

Required changes:
1. Add `unit_system` option.
2. Switch `Fl_I:stat:W`, `Fl_I:tot:h`, and reactant enthalpy/mixed enthalpy ports to `get_unit`.
3. Preserve CS-safe array/math behavior.

## 7. Testing Strategy

## 7.1 Unit tests (new/expanded)

1. Registry tests
- verify all required unit keys exist in both systems.

2. Component parity tests
- inlet/nozzle/turbine/shaft/performance/map interfaces.

3. Derivative tests
- run `check_partials` in ENG and SI for migrated components.

## 7.2 Integration tests

1. Mini-cycle ENG vs SI equivalence with strict tolerances.
2. Example-cycle smoke tests in both systems:
- electric propulsor
- simple turbojet
- multi-spool turboshaft

3. Extended sweeps (non-blocking but recommended):
- afterburning turbojet
- high bypass turbofan
- mixed-flow turbofan

## 7.3 Reporting

Generate or refresh:
- `docs/units_examples_report.md`

Include:
- convergence status,
- key metrics in native units and converted parity check,
- known deltas and causes.

## 8. Backward Compatibility and Deprecation

1. Keep default `unit_system='ENG'`.
2. Keep compatibility aliases:
- `EngUnitProps`
- `EngUnitStaticProps`
3. Keep deprecated `g_c` symbol in `constants.py` for one release with warning if accessed.
4. Do not remove legacy names until tests and docs are fully migrated.

## 9. Risks and Mitigations

1. Risk: silent equation regressions during unit refactor.
- Mitigation: mandatory ENG/SI parity checks and derivative checks per component.

2. Risk: map behavior drift due to flow-unit changes.
- Mitigation: lock map normalization definitions and compare interpolated map outputs pre/post.

3. Risk: complex-step breakage.
- Mitigation: avoid forced float casts and in-place ops that block complex dtype.

4. Risk: partial conversion creates mixed interfaces.
- Mitigation: phase by component family and gate merges on dual-system tests.

## 10. Execution Checklist

1. Phase A complete:
- All runtime IO declarations unit-aware.

2. Phase B complete:
- No ENG-only conversion assumptions left in equations.

3. Phase C complete:
- Viewers/docs/output formatting dual-system consistent.

4. Phase D complete:
- CI dual-system regression gates enabled.

5. Final acceptance:
- All target examples run in ENG and SI with equivalent physics.

## 11. Recommended Tracking in `docs/PRIORITIES.md`

Use the existing IDs and add sub-status notes:
1. `UNI-01` DONE (implemented).
2. `UNI-03` DONE (implemented).
3. `UNI-04` DONE for inlet/nozzle `g_c` removal; residual unit-hardcoding in other modules tracked under new sub-items.
4. Add follow-up items:
- `UNI-06` Runtime component declaration unification.
- `UNI-07` Map and power/torque convention unification.
- `UNI-08` Dual-system derivative coverage.
- `UNI-09` Full example matrix certification.

## 12. Immediate Next Sprint (Practical Cut)

1. Convert runtime declarations in:
- nozzle remaining subcomponents,
- turbine internals,
- shaft,
- performance,
- map components.

2. Add/expand tests:
- component parity + partials for migrated modules.

3. Re-run matrix:
- electric propulsor, simple turbojet, multi-spool turboshaft in ENG and SI.

4. Refresh docs:
- this file,
- `docs/units_examples_report.md`,
- `docs/QUICK_REFERENCE.md`,
- `docs/RUNNING_EXAMPLES.md`.
