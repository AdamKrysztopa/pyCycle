# Code Quality Findings

## TODOs in Codebase

13 TODO comments found across the codebase. These represent acknowledged technical debt:

| File | Line | TODO | Severity |
|------|------|------|----------|
| [`element_base.py`](../../pycycle/element_base.py:57) | 57 | Compare all ports to port data at end of setup — ensure nothing missing | MEDIUM |
| [`flow_in.py`](../../pycycle/flow_in.py:46) | 46 | Move V, Vsonic, MN, area, Wc, W out of static namespace — keep top level | MEDIUM |
| [`mp_cycle.py`](../../pycycle/mp_cycle.py:70) | 70 | Error check based on `_base_class_super_called` | LOW |
| [`mp_cycle.py`](../../pycycle/mp_cycle.py:210) | 210 | Throw error if `pyc_add_cycle_param` is called after setup | MEDIUM |
| [`thermo.py`](../../pycycle/thermo/thermo.py:57) | 57 | Remove `n`, `n_moles` variable from flow station | HIGH |
| [`thermo.py`](../../pycycle/thermo/thermo.py:84) | 84 | Add T/P range bounds to tabular thermo | MEDIUM |
| [`thermo.py`](../../pycycle/thermo/thermo.py:122) | 122 | Move Newton solver into convergence sub-group | LOW |
| [`thermo.py`](../../pycycle/thermo/thermo.py:132) | 132-139 | Remove need for thermo-specific data in flow components — 2 instances | MEDIUM |
| [`chem_eq.py`](../../pycycle/thermo/cea/chem_eq.py:215) | 215 | Talk to John about n_moles not getting set in apply_linear | HIGH |
| [`test_thermo_total_static_cea.py`](../../pycycle/thermo/test/test_thermo_total_static_cea.py:53) | 53 | Investigate weirdness — case won't work if thermo_TP fully solves | HIGH |
| [`test_thermo_total_static_tabulated.py`](../../pycycle/thermo/test/test_thermo_total_static_tabulated.py:55) | 55 | Same weirdness as above — duplicated TODO | HIGH |
| [`test_cooling.py`](../../pycycle/elements/test/test_cooling.py:140) | 140 | Set correct values for Pt_out and ht_out assertions | MEDIUM |

### Critical TODOs

The `n_moles` issue in [`chem_eq.py`](../../pycycle/thermo/cea/chem_eq.py:215) and the test weirdness in thermo tests suggest **potential correctness issues** in the CEA thermodynamic calculations. These should be investigated before other improvements.

## Deprecated Code

### Still Active

| Item | Location | Deprecation Target | Status |
|------|----------|-------------------|--------|
| [`DeprecatedDict`](../../pycycle/constants.py:6) class | `constants.py` | "pyCycle 4.0" | Still active in 4.4.x |
| [`AIR_FUEL_MIX`](../../pycycle/constants.py:49) | `constants.py` | `CEA_AIR_FUEL_COMPOSITION` | Still exported in `api.py` |
| [`AIR_MIX`](../../pycycle/constants.py:50) | `constants.py` | `CEA_AIR_COMPOSITION` | Still exported in `api.py` |
| [`WET_AIR_MIX`](../../pycycle/constants.py:51) | `constants.py` | `CEA_WET_AIR_COMPOSITION` | Still exported in `api.py` |
| [`connect_flow()`](../../pycycle/connect_flow.py:4) | `connect_flow.py` | `pyc_connect_flow` | Still imported in `api.py` |
| [`pyc_add_element()`](../../pycycle/mp_cycle.py:40) | `mp_cycle.py` | `add_subsystem` | Still present |

**Assessment**: All deprecations reference "pyCycle 4.0" but the current version is 4.4.x. These should have been removed several minor versions ago.

### Deprecated Warning Pattern

The deprecated warning pattern is inconsistent:

```python
# Pattern used in connect_flow.py and mp_cycle.py
warnings.simplefilter('always', DeprecationWarning)
warnings.warn("...")
warnings.simplefilter('ignore', DeprecationWarning)
```

This temporarily enables warnings then immediately suppresses them, which interacts badly with user code that may have its own warning filters.

## Code Smells

### 1. Empty Test File

[`pycycle/tests/test_element.py`](../../pycycle/tests/test_element.py) contains only:

```python
import unittest
```

One line. No tests. The `Element` base class has zero test coverage.

### 2. MapData Anti-Pattern

[`map_data.py`](../../pycycle/maps/map_data.py:1) — the self-described "stupid hack":

```python
# stupid hack so I can create data containers in python
class MapData(object):
    pass
```

This should be a `dataclass` or `NamedTuple` with validated fields.

### 3. FlowIn Dummy Output

[`flow_in.py`](../../pycycle/flow_in.py:21) — framework workaround:

```python
self.add_output('foo', val=1.,
    desc="dummy output that is NOT used for anything other than to keep the framework happy.")
```

### 4. String Formatting Inconsistency

The codebase mixes three string formatting styles:

```python
# %-formatting (oldest)
'%s:tot:%s' % (fl_name, v_name)           # flow_in.py, mp_cycle.py

# .format()
'{0}:{1}'.format(fl_name, in_name)          # unit_comps.py
'trq_{:d}'.format(i)                        # shaft.py

# f-strings (newest)
f'{fl_src}:tot:composition'                 # mp_cycle.py
f'{fl_out_name}:stat:{prop}'                # nozzle.py
```

This should be standardised to f-strings.

### 5. `super()` Usage Inconsistency

```python
# Old-style
super(PassThrough, self).__init__()         # passthrough.py:13
super(MPCycle, self).__init__(**kwargs)      # mp_cycle.py:205

# New-style
super().__init__(**kwargs)                   # element_base.py:16
```

### 6. Commented-Out Code

Multiple files contain extensive commented-out code:

- [`turbine.py`](../../pycycle/elements/turbine.py:64) — alternative Rt calculation approaches
- [`thermo.py`](../../pycycle/thermo/thermo.py:177) — alternative linesearch configuration
- [`flow_in.py`](../../pycycle/flow_in.py:54) — WAR and viscosity inputs
- [`test_cooling.py`](../../pycycle/elements/test/test_cooling.py:140) — incomplete assertions

### 7. Undefined Reference

[`turbine.py`](../../pycycle/elements/turbine.py:43) references `AnalysisError` without importing it:

```python
except FloatingPointError:
    raise AnalysisError('Bad values...')  # AnalysisError is not imported!
```

This will produce a `NameError` at runtime if the `FloatingPointError` is triggered.

### 8. Inconsistent Element Hierarchy

| Element | Base Class | Has Flow Ports |
|---------|-----------|---------------|
| Compressor | `Element` | Yes |
| Turbine | `Element` | Yes |
| Combustor | `Element` | Yes |
| Nozzle | `Element` | Yes |
| Inlet | `Element` | Yes |
| Duct | `Element` | Yes |
| Mixer | `Element` | Yes |
| Splitter | `Element` | Yes |
| BleedOut | `Element` | Yes |
| **Shaft** | **`ExplicitComponent`** | **No** |
| **Performance** | **`ExplicitComponent`** | **No** |
| **Gearbox** | **`ExplicitComponent`** | **No** |
| **FlightConditions** | **`Element`** | **Yes** |

`Shaft`, `Performance`, and `Gearbox` don't extend `Element` — they're direct `ExplicitComponent` subclasses. This is architecturally inconsistent even though these components don't have flow ports.

## Test Coverage Assessment

### Unit Tests

| Module | Test File | Coverage |
|--------|-----------|----------|
| `element_base.py` | `test_element.py` | **EMPTY** — zero tests |
| `mp_cycle.py` | none | **NONE** — no dedicated tests |
| `api.py` | none | **NONE** — no import/smoke tests |
| `viewers.py` | none | **NONE** — no tests |
| `passthrough.py` | none | Has `__main__` block but no test file |
| `connect_flow.py` | none | **NONE** |
| `constants.py` | none | **NONE** |
| Elements | `elements/test/` | GOOD — 22 test files, regression data |
| Thermo CEA | `thermo/cea/test/` | MODERATE — 5 test files |
| Maps | `maps/test/` | **EMPTY** — `__init__.py` only |

### Integration Tests

| Test | Location | Coverage |
|------|----------|----------|
| Example benchmarks | `example_cycles/tests/` | GOOD — 10 benchmark files |
| Full cycle tests | `example_cycles/tests/test_all_examples.py` | MODERATE — runs all examples |
| Cross-platform | GitHub Actions | Ubuntu, macOS, Windows |

### Gaps

1. **Zero core module tests** — `element_base`, `mp_cycle`, `api`, `viewers`, `connect_flow`, `constants`
2. **Zero map tests** — `pycycle/maps/test/` is empty
3. **No negative tests** — no tests for invalid inputs, bad configurations, or error paths
4. **No performance tests** — no benchmarks for solver convergence speed
5. **Commented-out assertions** — test_cooling.py has incomplete validations

## Build & CI Issues

### Dual Build Configuration

| Aspect | `setup.py` | `pyproject.toml` |
|--------|-----------|-----------------|
| Version | Reads from `__init__.py` | Uses `setuptools_scm` |
| Dependencies | `openmdao>=3.10.0` only | `openmdao>=3.10.0`, `numpy>=1.20.0`, `scipy>=1.7.0` |
| Dev deps | `testflo`, `parameterized` | `testflo`, `parameterized`, `pytest`, `black`, `flake8`, `mypy` |
| Package data | Defined | Defined — duplicated |

**Recommendation**: Remove `setup.py`; `pyproject.toml` is the modern standard.

### Stale Travis CI

[`.travis.yml`](.travis.yml):
- References Python 3.6 — EOL since December 2021
- Uses Miniconda installer that may not exist
- Duplicates what GitHub Actions already does

**Recommendation**: Delete `.travis.yml`.

### GitHub Actions Coverage

[`pycycle_test_workflow.yml`](../../.github/workflows/pycycle_test_workflow.yml):
- Tests on Ubuntu, macOS, Windows ✓
- Tests with NumPy 1.26 and 2.x ✓
- Runs deprecation report ✓
- Runs NumPy 2.0 compatibility check with ruff ✓
- **Missing**: No coverage report upload — to Codecov or similar
- **Missing**: No lint/format checks — despite `black` and `flake8` in dev deps
- **Missing**: No mypy type checking — despite `mypy` in dev deps

## Summary Statistics

| Metric | Count |
|--------|-------|
| TODO comments | 13 |
| Deprecated items still present | 6 |
| Code smells identified | 8 |
| Empty/missing test files | 6+ |
| Type hints | 0 |
| Docstrings with parameters documented | ~3 — only [`viewers.py`](../../pycycle/viewers.py:14) has proper docstrings |
