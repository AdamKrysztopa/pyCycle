# Improvement Plan: Documentation

**Related audit**: [Maintainability Risk](../audit/07_risk_maintainability.md), [Code Quality Findings](../audit/08_code_quality_findings.md)  
**Related PRs**: PR 10 — Documentation & Refactoring

---

## DOC-01: Sphinx API Reference Expansion

**Current state**: Sphinx docs are minimal. Only a few entries exist in `pycycle/docs/reference_guide/` and the API surface in [`pycycle/api.py`](../../pycycle/api.py) is not documented.

**Improvement**: Build full API reference pages:

- `pycycle/docs/reference_guide/elements/` should include one page per element:
  - `ambient`, `bleed_out`, `cfd_start`, `combustor`, `compressor`, `compressor_map`, `cooling`, `duct`, `flight_conditions`, `flow_start`, `gearbox`, `inlet`, `mixer`, `nozzle`, `performance`, `shaft`, `splitter`, `turbine`, `turbine_map`, `US1976`
- `pycycle/docs/reference_guide/maps/` should include map types and an index table
- Add `reference_guide/thermo/` for CEA + Tabular
- Add `reference_guide/core/` for `Cycle`, `MPCycle`, `Element`, `FlowIn`, `connect_flow`

**Files to modify**:
- [`pycycle/docs/index.rst`](../../pycycle/docs/index.rst) — add sections
- [`pycycle/docs/reference_guide/elements/index.rst`](../../pycycle/docs/reference_guide/elements/index.rst) — add entries
- [`pycycle/docs/reference_guide/maps/index.rst`](../../pycycle/docs/reference_guide/maps/index.rst) — add entries

**Files to create**: new `.rst` files under `reference_guide/`

**Depends on**: DX-01 (docstring standards)  
**Risk**: LOW

---

## DOC-02: Tutorial Expansion

**Current state**: Only one detailed tutorial exists: [`turbojet.rst`](../../pycycle/docs/tutorials/turbojet.rst). A stub exists for turbofan.

**Improvement**:
1. **Turbofan tutorial** — complete the existing stub: `turbofan.rst`
2. **Turboshaft tutorial** — new example covering multi-spool shaft coupling
3. **Afterburning turbojet** — after new element is implemented
4. **Electric propulsor** — document how electric power and performance are configured
5. **Map tuning tutorial** — selecting/designing compressor/turbine maps

**Files to modify**:
- [`pycycle/docs/tutorials/index.rst`](../../pycycle/docs/tutorials/index.rst) — add new tutorials
- [`pycycle/docs/tutorials/turbofan.rst`](../../pycycle/docs/tutorials/turbofan.rst) — expand

**Files to create**: new `.rst` tutorials

**Depends on**: PHY-01 (afterburner) for afterburner tutorial  
**Risk**: LOW

---

## DOC-03: Usage Cookbook

**Current state**: No concise “cookbook” for common tasks (setting balance variables, connecting flows, switching thermo method).

**Improvement**: Add `docs/cookbook.md` or `pycycle/docs/cookbook.rst` with short recipes:

- Add a new element to a cycle
- Set up design vs off-design points
- Switch between CEA and tabular thermo
- Create and connect a bleed stream
- Use `Cycle.pyc_add_element` and `Cycle.pyc_connect_flow`
- Set solver options for hard cases
- Save and reload map scaling

**Files to create**: `pycycle/docs/cookbook.rst` or `docs/cookbook.md`  
**Depends on**: None  
**Risk**: LOW

---

## DOC-04: Flow Station Output Reference

**Current state**: No central list of flow station variables or their meanings.

**Improvement**: Add a flow station reference table with variable names, units, and definitions:

| Variable | Meaning | Units | Notes |
|---------|---------|-------|-------|
| `Tt` | Total temperature | degR/degK | Design or off-design |
| `Pt` | Total pressure | psi/Pa |   |
| `ht` | Total enthalpy | Btu/lbm or J/kg |   |
| `W` | Mass flow | lbm/s or kg/s |   |
| `MN` | Mach number | - |   |
| `V` | Velocity | ft/s or m/s |   |

**Files to create**: `pycycle/docs/reference_guide/flow_station.rst`  
**Depends on**: UNI-03 (flow unit outputs)  
**Risk**: LOW

---

## DOC-05: Developer Onboarding

**Current state**: README provides installation and overview but lacks contributor workflow details.

**Improvement**: Add `CONTRIBUTING.md`:

- Local setup
- Running tests
- Building docs
- Coding conventions
- How to add a new element
- How to add a new map
- Regression test workflow

**Files to create**: [`CONTRIBUTING.md`](../../CONTRIBUTING.md)  
**Depends on**: DX-03 (formatting), TST-06 (CI coverage)  
**Risk**: LOW

---

## DOC-06: Example Gallery

**Current state**: Examples exist but are not cataloged in docs.

**Improvement**: Add a “Gallery” page in docs that lists each example cycle:

- `simple_turbojet`
- `afterburning_turbojet`
- `high_bypass_turbofan`
- `mixedflow_turbofan`
- `single_spool_turboshaft`
- `multi_spool_turboshaft`
- `wet_propulsor`
- `electric_propulsor`
- `N+3ref` benchmarks

**Files to create**: `pycycle/docs/examples/gallery.rst`  
**Files to modify**: [`pycycle/docs/examples/index.rst`](../../pycycle/docs/examples/index.rst)  
**Depends on**: None  
**Risk**: LOW

---

## DOC-07: API Deprecation Policy

**Current state**: Deprecations exist but without a documented policy.

**Improvement**: Document deprecation lifecycle:

1. Deprecation warnings added
2. Deprecation timeline — minimum 2 releases
3. Removal notice in `release_notes.md`
4. Migration guide updates

**Files to modify**: [`release_notes.md`](../../release_notes.md), [`README.md`](../../README.md)  
**Depends on**: None  
**Risk**: LOW

---

## Summary

| ID | Improvement | Priority | Risk | Phase |
|----|------------|----------|------|-------|
| DOC-01 | Sphinx API reference expansion | HIGH | LOW | 1 |
| DOC-02 | Tutorial expansion | MEDIUM | LOW | 2 |
| DOC-03 | Usage cookbook | MEDIUM | LOW | 1 |
| DOC-04 | Flow station output reference | MEDIUM | LOW | 1 |
| DOC-05 | Developer onboarding | MEDIUM | LOW | 1 |
| DOC-06 | Example gallery | LOW | LOW | 2 |
| DOC-07 | Deprecation policy | LOW | LOW | 2 |
