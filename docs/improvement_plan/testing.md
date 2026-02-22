# Improvement Plan: Testing

**Related audit**: [Code Quality Findings](../audit/08_code_quality_findings.md)  
**Related PRs**: PR 10 — Documentation & Refactoring

---

## TST-01: Core Module Unit Tests

**Current state**: Zero tests for core modules — [`element_base.py`](../../pycycle/element_base.py), [`mp_cycle.py`](../../pycycle/mp_cycle.py), [`api.py`](../../pycycle/api.py), [`viewers.py`](../../pycycle/viewers.py), [`connect_flow.py`](../../pycycle/connect_flow.py), [`constants.py`](../../pycycle/constants.py). [`pycycle/tests/test_element.py`](../../pycycle/tests/test_element.py) is a single `import unittest` line.

**Improvement**: Create test files for each core module:

### `pycycle/tests/test_element_base.py`
```python
class TestElement(unittest.TestCase):
    def test_flow_data_init(self):
        """Element initialises with empty Fl_I_data and Fl_O_data."""
    
    def test_copy_flow_from_string(self):
        """copy_flow with string src_port copies from Fl_I_data."""
    
    def test_copy_flow_from_thermo_add(self):
        """copy_flow with ThermoAdd queries output_port_data."""
    
    def test_copy_flow_invalid_type(self):
        """copy_flow with invalid type raises ValueError."""
    
    def test_init_output_flow(self):
        """init_output_flow sets Fl_O_data correctly."""
```

### `pycycle/tests/test_mp_cycle.py`
```python
class TestCycle(unittest.TestCase):
    def test_add_subsystem_tracks_elements(self):
        """Element subclasses are tracked in _elements set."""
    
    def test_add_subsystem_non_element(self):
        """Non-Element subsystems are not tracked in _elements."""
    
    def test_thermo_method_propagation(self):
        """Cycle thermo_method propagates to child elements."""
    
    def test_pyc_connect_flow_builds_graph(self):
        """pyc_connect_flow creates correct graph structure."""
    
    def test_flow_graph_bfs(self):
        """setup() traverses flow graph in correct BFS order."""
    
    def test_deprecated_pyc_add_element(self):
        """pyc_add_element emits DeprecationWarning."""

class TestMPCycle(unittest.TestCase):
    def test_single_design_point(self):
        """Only one design point allowed."""
    
    def test_multiple_od_points(self):
        """Multiple off-design points can be added."""
    
    def test_cycle_param_promotion(self):
        """Cycle params promoted to all points."""
    
    def test_des_od_connections(self):
        """Design-to-OD connections are issued correctly."""
```

### `pycycle/tests/test_api.py`
```python
class TestApiImports(unittest.TestCase):
    def test_all_elements_importable(self):
        """All public elements can be imported from pycycle.api."""
    
    def test_all_maps_importable(self):
        """All public maps can be imported from pycycle.api."""
    
    def test_all_constants_importable(self):
        """All public constants can be imported from pycycle.api."""
```

### `pycycle/tests/test_viewers.py`
```python
class TestViewers(unittest.TestCase):
    def test_get_val_normal(self):
        """get_val returns correct value from problem."""
    
    def test_get_val_cycle_param(self):
        """get_val falls back to cycle parameter on KeyError."""
    
    def test_print_flow_station(self):
        """print_flow_station produces formatted output."""
```

### `pycycle/tests/test_constants.py`
```python
class TestConstants(unittest.TestCase):
    def test_air_jeta_tab_spec_loaded(self):
        """AIR_JETA_TAB_SPEC loads successfully and has expected keys."""
    
    def test_composition_dicts(self):
        """CEA compositions have expected elements."""
    
    def test_physical_constants(self):
        """Physical constants have correct values."""
```

**Files to create**: 5 test files in `pycycle/tests/`  
**Files to modify**: [`pycycle/tests/test_element.py`](../../pycycle/tests/test_element.py) — rewrite  
**Depends on**: Nothing  
**Risk**: NONE

---

## TST-02: Map Tests

**Current state**: [`pycycle/maps/test/__init__.py`](../../pycycle/maps/test/__init__.py) exists but the directory has no test files.

**Improvement**: Create tests for map infrastructure:

```python
# pycycle/maps/test/test_map_data.py
class TestMapData(unittest.TestCase):
    def test_axi5_loads(self):
        """AXI5 map loads with correct shapes."""
    
    def test_axi5_shapes_consistent(self):
        """WcMap, effMap, PRmap shapes match axis arrays."""
    
    def test_lpt2269_loads(self):
        """LPT2269 turbine map loads correctly."""
    
    def test_all_maps_have_defaults(self):
        """All maps have a defaults dict with required keys."""
```

**Files to create**: `pycycle/maps/test/test_map_data.py`  
**Depends on**: Nothing  
**Risk**: NONE

---

## TST-03: Complete Cooling Test Assertions

**Current state**: [`test_cooling.py`](../../pycycle/elements/test/test_cooling.py:140) has commented-out assertions:

```python
assert_near_equal(p['W_cool'], 4.44635, tol)
# assert_near_equal(self, p['Pt_out'], 4.44635, tol) # TODO: set this
# assert_near_equal(self, p['ht_out'], 4.44635, tol)
```

**Improvement**:
1. Determine correct reference values for `Pt_out` and `ht_out` — either from NPSS comparison or analytic calculation
2. Uncomment and set correct expected values
3. Add additional assertions for stage temperature and pressure

**Files to modify**: [`pycycle/elements/test/test_cooling.py`](../../pycycle/elements/test/test_cooling.py)  
**Depends on**: Nothing  
**Risk**: LOW

---

## TST-04: Negative Tests

**Current state**: No tests for invalid inputs, bad configurations, or error paths.

**Improvement**: Add negative tests:

```python
class TestElementErrors(unittest.TestCase):
    def test_invalid_thermo_method(self):
        """Invalid thermo_method raises ValueError."""
    
    def test_missing_flow_connection(self):
        """Missing flow connection produces clear error."""

class TestCycleErrors(unittest.TestCase):
    def test_duplicate_design_point(self):
        """Adding second design point raises ValueError."""
    
    def test_des_od_connect_without_design(self):
        """Connecting before design point raises ValueError."""
    
    def test_cycle_param_after_setup(self):
        """Adding cycle param after setup raises error."""  # TODO from mp_cycle.py:210
```

**Files to create**: `pycycle/tests/test_errors.py`  
**Depends on**: Nothing  
**Risk**: NONE

---

## TST-05: Fix Undefined `AnalysisError` Reference

**Current state**: [`turbine.py`](../../pycycle/elements/turbine.py:43) catches `FloatingPointError` and raises `AnalysisError` — which is not imported:

```python
except FloatingPointError:
    raise AnalysisError('Bad values...')  # NameError at runtime!
```

**Improvement**: 
1. Add the import: `from openmdao.core.analysis_error import AnalysisError`
2. Add a test that triggers the `FloatingPointError` path to verify it works

**Files to modify**: [`pycycle/elements/turbine.py`](../../pycycle/elements/turbine.py)  
**Depends on**: Nothing  
**Risk**: LOW

---

## TST-06: CI Coverage Reporting

**Current state**: [`pycycle_test_workflow.yml`](../../.github/workflows/pycycle_test_workflow.yml) runs `--coverage` flag but does not upload results to a coverage service.

**Improvement**: Add coverage upload step:

```yaml
- name: Upload coverage
  if: ${{ ! matrix.EXCLUDE }}
  uses: codecov/codecov-action@v4
  with:
    flags: unittests
    fail_ci_if_error: false
```

Also add a coverage badge to `README.md`.

**Files to modify**: [`.github/workflows/pycycle_test_workflow.yml`](../../.github/workflows/pycycle_test_workflow.yml)  
**Depends on**: Nothing  
**Risk**: NONE

---

## TST-07: CI Lint and Type Check Steps

**Current state**: `black`, `flake8`, and `mypy` are in dev dependencies but not used in CI.

**Improvement**: Add CI steps:

```yaml
- name: Check formatting
  run: black --check pycycle/

- name: Lint
  run: flake8 pycycle/ --max-line-length=100

- name: Type check
  run: mypy pycycle/ --ignore-missing-imports
```

**Files to modify**: [`.github/workflows/pycycle_test_workflow.yml`](../../.github/workflows/pycycle_test_workflow.yml)  
**Depends on**: DX-01 — type hints; DX-03 — formatting  
**Risk**: LOW — may initially fail if code isn't formatted/typed

---

## TST-08: Thermo Weirdness Investigation

**Current state**: Two test files have the same TODO:
- [`test_thermo_total_static_cea.py`](../../pycycle/thermo/test/test_thermo_total_static_cea.py:53)
- [`test_thermo_total_static_tabulated.py`](../../pycycle/thermo/test/test_thermo_total_static_tabulated.py:55)

> "Investigate this weirdness.... this case won't work if you thermo_TP fully solve itself"

**Improvement**:
1. Investigate why `thermo_TP` solving fully causes test failures
2. Document the root cause
3. Either fix the underlying issue or document it as a known limitation with a clear comment
4. Remove the "weirdness" TODO

**Files to modify**: 
- [`pycycle/thermo/test/test_thermo_total_static_cea.py`](../../pycycle/thermo/test/test_thermo_total_static_cea.py)
- [`pycycle/thermo/test/test_thermo_total_static_tabulated.py`](../../pycycle/thermo/test/test_thermo_total_static_tabulated.py)

**Depends on**: Nothing  
**Risk**: MEDIUM — may reveal deeper thermo issues

---

## TST-09: Performance Benchmarks

**Current state**: Example benchmarks exist in `example_cycles/tests/` but measure correctness, not performance. No timing or convergence-speed benchmarks.

**Improvement**: Add performance benchmark suite:

```python
class PerformanceBenchmarks(unittest.TestCase):
    def test_turbojet_convergence_speed(self):
        """Turbojet design point converges in < 10 Newton iterations."""
    
    def test_tabular_vs_cea_speedup(self):
        """Tabular thermo is at least 5x faster than CEA."""
    
    def test_turbofan_solve_time(self):
        """Turbofan design point solves in < 5 seconds."""
```

**Files to create**: `pycycle/tests/test_benchmarks.py`  
**Depends on**: Nothing  
**Risk**: NONE

---

## Summary

| ID | Improvement | Priority | Risk | Phase |
|----|------------|----------|------|-------|
| TST-01 | Core module unit tests | HIGH | NONE | 1 |
| TST-02 | Map tests | HIGH | NONE | 1 |
| TST-03 | Complete cooling assertions | MEDIUM | LOW | 1 |
| TST-04 | Negative tests | MEDIUM | NONE | 1 |
| TST-05 | Fix `AnalysisError` import | HIGH | LOW | 1 |
| TST-06 | CI coverage reporting | MEDIUM | NONE | 1 |
| TST-07 | CI lint and type check | MEDIUM | LOW | 1 |
| TST-08 | Thermo weirdness investigation | HIGH | MEDIUM | 1 |
| TST-09 | Performance benchmarks | LOW | NONE | 2 |
