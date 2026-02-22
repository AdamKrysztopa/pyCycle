# Risk 6: Maintainability & User Experience

**Severity**: MEDIUM  
**Impact**: High barrier to entry; extensive boilerplate required; limited documentation

## Current State in pyCycle

### Cycle and MPCycle Classes

[`Cycle`](../../pycycle/mp_cycle.py:13) provides:
- `add_subsystem()` — overridden to track elements and propagate thermo options
- `pyc_connect_flow()` — connects all flow variables between ports and builds flow graph
- `setup()` — BFS traversal of flow graph to propagate thermo configuration

[`MPCycle`](../../pycycle/mp_cycle.py:197) provides:
- `pyc_add_pnt()` — adds design or off-design operating points
- `pyc_add_cycle_param()` — promotes parameters across all points
- `pyc_connect_des_od()` — connects design outputs to off-design inputs
- `pyc_use_default_des_od_conns()` — auto-connects standard design→OD variables

### API Surface

[`pycycle/api.py`](../../pycycle/api.py) re-exports all public classes and constants. Users interact via:

```python
import pycycle.api as pyc
cycle = pyc.Cycle(design=True)
cycle.add_subsystem('fc', pyc.FlightConditions())
# ... 20-50 lines of add_subsystem() + pyc_connect_flow() + connect()
```

### Examples as Documentation

The repository self-describes its docs as "nearly non-existent" in [`README.md`](../../README.md:11). The primary learning resources are:
- Example scripts in `example_cycles/` — heavily relied upon
- One research paper — the MDPI Aerospace 2019 publication
- Sphinx docs in `pycycle/docs/` — mostly stubs with minimal content

### Sphinx Documentation State

The Sphinx docs in [`pycycle/docs/`](../../pycycle/docs/) contain:
- [`index.rst`](../../pycycle/docs/index.rst) — top-level page with section links
- [`tutorials/turbojet.rst`](../../pycycle/docs/tutorials/turbojet.rst) — brief turbojet tutorial
- [`tutorials/turbofan.rst`](../../pycycle/docs/tutorials/turbofan.rst) — placeholder — 276 chars
- [`reference_guide/elements/index.rst`](../../pycycle/docs/reference_guide/elements/index.rst) — element list stub
- [`reference_guide/maps/index.rst`](../../pycycle/docs/reference_guide/maps/index.rst) — map reference stub

Most pages are essentially empty or link to non-existent pages.

## Identified Issues

### 1. Excessive Boilerplate for Cycle Assembly

Building a simple turbojet requires ~150 lines of code in [`simple_turbojet.py`](../../example_cycles/simple_turbojet.py):
- ~8 `add_subsystem()` calls
- ~5 `pyc_connect_flow()` calls
- ~10 `connect()` calls for non-flow connections
- ~15 lines for balance components
- ~20 lines for solver configuration
- ~30 lines for setting initial values

A turbofan requires ~350 lines. Users must understand OpenMDAO internals to configure solvers, set `guess` variables, and manage the balance/residual structure.

### 2. No Configuration-Driven Approach

There is no way to define an engine via a configuration file or dictionary. Every engine requires Python code. This prevents:
- Non-programmer use — e.g., configuration via JSON/YAML
- Parametric studies with configuration files
- Engine template libraries
- Validation against a schema

### 3. No Type Hints

Zero type annotations in the entire codebase — verified by searching for `->` and type annotation patterns:
- No function return types
- No parameter types
- No variable annotations
- No `Protocol` or `TypeVar` usage

This prevents:
- IDE autocompletion
- Static analysis with mypy — despite mypy being in dev dependencies
- Self-documenting code
- Catching type errors early

### 4. Inconsistent Error Messages

Error handling varies across components:
- Some raise `RuntimeError` with context — [`mp_cycle.py`](../../pycycle/mp_cycle.py:148)
- Some silently produce bad values — `CorrectedInputsCalc` in turbine catches `FloatingPointError` but references undefined `AnalysisError`
- Some have no error handling at all

### 5. FlowIn Dummy Output

[`FlowIn`](../../pycycle/flow_in.py:21) has:

```python
self.add_output('foo', val=1.,
    desc="dummy output that is NOT used for anything other than to keep the framework happy.")
```

This hack exists because OpenMDAO requires at least one output. It's a code smell and framework workaround.

### 6. Dual Build System

Both [`setup.py`](../../setup.py) and [`pyproject.toml`](../../pyproject.toml) define package metadata:
- `setup.py` reads version from `pycycle/__init__.py` — but `pyproject.toml` uses `setuptools_scm`
- Dependencies differ slightly between the two files
- Modern Python only needs `pyproject.toml`

### 7. Stale CI Configuration

[`.travis.yml`](.travis.yml) references Python 3.6 and Miniconda — completely outdated. The actual CI is in [`.github/workflows/pycycle_test_workflow.yml`](../../.github/workflows/pycycle_test_workflow.yml) using GitHub Actions with Python 3.12.

### 8. Deprecated Code Not Removed

Despite being at version 4.4.x — well past the "pyCycle 4.0" deprecation target:
- [`DeprecatedDict`](../../pycycle/constants.py:6) still warns about "pyCycle 4.0" replacement
- [`connect_flow()`](../../pycycle/connect_flow.py:4) is deprecated but still exported
- [`pyc_add_element()`](../../pycycle/mp_cycle.py:40) is deprecated but still present

## What Is Missing

| Gap | Description | Priority |
|-----|-------------|----------|
| High-level API | `simulate()` / `sweep()` functions | HIGH |
| Type hints | Annotations across all modules | HIGH |
| Configuration schema | JSON/YAML/Pydantic engine definition | MEDIUM |
| Template engine builders | `build_turbofan(config)` factory functions | MEDIUM |
| Error consistency | Standardised error hierarchy | MEDIUM |
| Remove deprecated code | Clean up post-4.0 deprecations | LOW |
| Remove `setup.py` | Use only `pyproject.toml` | LOW |
| Remove `.travis.yml` | Stale CI config | LOW |

## Proposed Mitigations

### High-Level API

Extend [`pycycle/api.py`](../../pycycle/api.py) with:

```python
def simulate(engine_config: dict, operating_point: dict) -> dict:
    """Build and run a cycle from a configuration dictionary."""

def sweep(engine_config: dict, sweep_params: dict) -> pd.DataFrame:
    """Run parametric sweep with warm-starting."""
```

### Configuration Schema

```python
@dataclass
class EngineConfig:
    name: str
    elements: list[ElementConfig]
    flow_connections: list[tuple[str, str]]
    design_variables: dict[str, float]
    thermo_method: str = 'TABULAR'
    unit_system: str = 'ENG'
```

### Template Builders

```python
def build_turbojet(bpr: float = 0.0, opr: float = 20.0, ...) -> Cycle:
    """Build a standard turbojet cycle with sensible defaults."""

def build_turbofan(bpr: float = 5.0, fpr: float = 1.6, ...) -> Cycle:
    """Build a standard turbofan cycle with sensible defaults."""
```

## Validation Approach

1. **API tests** — build engines via `simulate()` and compare with manually assembled cycles
2. **Schema validation** — test that invalid configs produce clear error messages
3. **Template tests** — verify template builders produce converging cycles
4. **Type checking** — run `mypy` as part of CI after adding type hints
5. **Deprecation removal tests** — ensure no tests rely on deprecated APIs

## Classification

| Mitigation | Type |
|-----------|------|
| High-level API | INTEGRATE — builds on top of existing architecture |
| Configuration schema | INTEGRATE — new module |
| Template builders | MITIGATE — optional helpers |
| Type hints | PATCH — incremental addition |
| Error standardisation | PATCH — incremental improvement |
| Cleanup — deprecated code, setup.py, travis | PATCH — removal of dead code |
