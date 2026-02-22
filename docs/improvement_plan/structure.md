# Improvement Plan: Structure & Architecture

**Related audit**: [Risk 6: Maintainability](../audit/07_risk_maintainability.md), [Architecture Overview](../audit/01_architecture_overview.md)  
**Related PRs**: PR 9 — High-Level API, PR 10 — Refactoring

---

## S-01: Consistent Element Hierarchy

**Current state**: [`Shaft`](../../pycycle/elements/shaft.py:6), [`Performance`](../../pycycle/elements/performance.py), and [`Gearbox`](../../pycycle/elements/gearbox.py) extend `ExplicitComponent` directly instead of [`Element`](../../pycycle/element_base.py:9).

**Improvement**: Create a `MechanicalElement` base — or mark non-flow elements explicitly:

```python
class MechanicalElement(om.ExplicitComponent):
    """Base class for non-flow mechanical elements like Shaft, Gearbox."""
    pass
```

**Files to modify**:
- [`pycycle/elements/shaft.py`](../../pycycle/elements/shaft.py) — change base class
- [`pycycle/elements/performance.py`](../../pycycle/elements/performance.py) — change base class
- [`pycycle/elements/gearbox.py`](../../pycycle/elements/gearbox.py) — change base class
- [`pycycle/element_base.py`](../../pycycle/element_base.py) — add `MechanicalElement`

**Depends on**: Nothing  
**Risk**: LOW

---

## S-02: Remove Dual Build System

**Current state**: Both [`setup.py`](../../setup.py) and [`pyproject.toml`](../../pyproject.toml) define package metadata with inconsistencies.

**Improvement**:
1. Delete [`setup.py`](../../setup.py)
2. Ensure [`pyproject.toml`](../../pyproject.toml) is complete — it already is
3. Verify `pip install -e .` works without `setup.py`

**Files to modify**:
- Delete `setup.py`
- Verify `pyproject.toml` — already correct

**Depends on**: Nothing  
**Risk**: LOW

---

## S-03: Remove Stale Travis CI

**Current state**: [`.travis.yml`](../../.travis.yml) references Python 3.6 and is superseded by GitHub Actions.

**Improvement**: Delete `.travis.yml`

**Files to modify**:
- Delete `.travis.yml`

**Depends on**: Nothing  
**Risk**: NONE

---

## S-04: Clean Up Deprecated Code

**Current state**: 6 deprecated items still active — see [Code Quality Findings](../audit/08_code_quality_findings.md).

**Improvement**:
1. Remove [`DeprecatedDict`](../../pycycle/constants.py:6) class — replace all usages with direct dict references
2. Remove deprecated aliases: `AIR_FUEL_MIX`, `AIR_MIX`, `WET_AIR_MIX`, `AIR_FUEL_ELEMENTS`, `AIR_ELEMENTS`, `WET_AIR_ELEMENTS`, `CO2_CO_O2_ELEMENTS`, `CO2_CO_O2_MIX`
3. Remove [`connect_flow()`](../../pycycle/connect_flow.py:4) — entire file
4. Remove [`pyc_add_element()`](../../pycycle/mp_cycle.py:40) method
5. Update [`api.py`](../../pycycle/api.py) to stop exporting deprecated names
6. Update any examples or tests that use deprecated APIs

**Files to modify**:
- [`pycycle/constants.py`](../../pycycle/constants.py)
- [`pycycle/connect_flow.py`](../../pycycle/connect_flow.py) — delete
- [`pycycle/mp_cycle.py`](../../pycycle/mp_cycle.py)
- [`pycycle/api.py`](../../pycycle/api.py)

**Depends on**: Nothing  
**Risk**: LOW — breaking change for users still using deprecated APIs

---

## S-05: Replace MapData with Dataclass

**Current state**: [`MapData`](../../pycycle/maps/map_data.py:3) is a bare `object` subclass — "stupid hack" per the comment.

**Improvement**: Replace with typed dataclasses:

```python
@dataclass
class CompressorMapData:
    alphaMap: np.ndarray
    NcMap: np.ndarray
    RlineMap: np.ndarray
    WcMap: np.ndarray
    effMap: np.ndarray
    PRmap: np.ndarray
    defaults: dict[str, float]
    RlineStall: float = 1.0

    def __post_init__(self):
        self._validate_shapes()

@dataclass
class TurbineMapData:
    alphaMap: np.ndarray
    NpMap: np.ndarray
    PRmap: np.ndarray
    WpMap: np.ndarray
    effMap: np.ndarray
    defaults: dict[str, float]

    def __post_init__(self):
        self._validate_shapes()
```

**Files to modify**:
- [`pycycle/maps/map_data.py`](../../pycycle/maps/map_data.py) — rewrite
- All map files in `pycycle/maps/` — update constructors
- [`pycycle/elements/compressor_map.py`](../../pycycle/elements/compressor_map.py)
- [`pycycle/elements/turbine_map.py`](../../pycycle/elements/turbine_map.py)

**Depends on**: Nothing  
**Risk**: MEDIUM — changes all map files

---

## S-06: Pickle Security — Lazy-Load Tabular Thermo Data

**Current state**: [`constants.py`](../../pycycle/constants.py:32) loads a pickle file at import time:

```python
with open(tab_spec_path, 'rb') as spec_data:
    AIR_JETA_TAB_SPEC = pickle.load(spec_data)
```

Pickle loading is a security concern — it executes arbitrary code — and the 485 KB file is loaded even if tabular thermo is never used.

**Improvement**:
1. Lazy-load the pickle — only when `TABULAR` thermo is requested
2. Consider switching to a safer format — JSON, msgpack, or compressed numpy arrays
3. Add integrity check — hash or checksum

```python
_AIR_JETA_TAB_SPEC = None

def get_air_jeta_tab_spec():
    global _AIR_JETA_TAB_SPEC
    if _AIR_JETA_TAB_SPEC is None:
        with open(tab_spec_path, 'rb') as spec_data:
            _AIR_JETA_TAB_SPEC = pickle.load(spec_data)
    return _AIR_JETA_TAB_SPEC

# For backwards compatibility
AIR_JETA_TAB_SPEC = property(lambda self: get_air_jeta_tab_spec())
```

**Files to modify**:
- [`pycycle/constants.py`](../../pycycle/constants.py)

**Depends on**: Nothing  
**Risk**: LOW

---

## S-07: High-Level API — `simulate()` and `sweep()`

**Current state**: Users must write 100-350 lines of boilerplate to build and run a cycle.

**Improvement**: Add convenience functions to [`pycycle/api.py`](../../pycycle/api.py):

```python
def simulate(engine_config: EngineConfig, operating_point: dict) -> SimResult:
    """Build cycle from config, run at operating point, return results."""

def sweep(engine_config: EngineConfig, sweep_params: dict[str, list]) -> pd.DataFrame:
    """Run parametric sweep with warm-starting across operating points."""
```

Add `EngineConfig` dataclass in new `pycycle/engine_config.py`:

```python
@dataclass
class ElementConfig:
    type: str          # 'compressor', 'turbine', 'combustor', etc.
    name: str          # instance name
    options: dict      # element-specific options
    map_data: str = None  # map name for turbomachinery

@dataclass
class EngineConfig:
    name: str
    elements: list[ElementConfig]
    flow_connections: list[tuple[str, str]]
    non_flow_connections: list[tuple[str, str]]
    design_variables: dict[str, Any]
    thermo_method: str = 'TABULAR'
    unit_system: str = 'ENG'
```

**Files to create**:
- `pycycle/engine_config.py`

**Files to modify**:
- [`pycycle/api.py`](../../pycycle/api.py)

**Depends on**: S-04 — cleanup; solver improvements  
**Risk**: LOW — additive, no breaking changes

---

## S-08: Template Engine Builders

**Current state**: No factory functions for common engine architectures.

**Improvement**: Add template builders:

```python
def build_turbojet(
    opr: float = 20.0,
    t4_max: float = 2800.0,  # degR
    design_alt: float = 0.0,  # ft
    design_mn: float = 0.0,
    thermo_method: str = 'TABULAR'
) -> Cycle:
    """Build a simple turbojet with sensible defaults."""

def build_turbofan(
    bpr: float = 5.0,
    fpr: float = 1.6,
    opr: float = 30.0,
    t4_max: float = 3000.0,
    thermo_method: str = 'TABULAR'
) -> Cycle:
    """Build a high-bypass turbofan with sensible defaults."""
```

**Files to create**:
- `pycycle/templates.py`

**Depends on**: S-07 — engine config  
**Risk**: LOW — additive

---

## S-09: FlowIn Dummy Output Cleanup

**Current state**: [`FlowIn`](../../pycycle/flow_in.py:21) has a dummy `foo` output to satisfy OpenMDAO.

**Improvement**: Check if newer OpenMDAO versions — ≥3.10 — still require at least one output. If so, use a more descriptive name. If not, remove it.

**Files to modify**:
- [`pycycle/flow_in.py`](../../pycycle/flow_in.py)

**Depends on**: OpenMDAO version check  
**Risk**: LOW

---

## S-10: Standardise String Formatting

**Current state**: Mix of `%`-formatting, `.format()`, and f-strings across codebase.

**Improvement**: Convert all to f-strings. This can be automated with `flynt` tool:

```bash
pip install flynt
flynt pycycle/
```

**Files to modify**: All `.py` files in `pycycle/`  
**Depends on**: Nothing  
**Risk**: NONE — cosmetic change

---

## S-11: Standardise `super()` Calls

**Current state**: Mix of `super(ClassName, self).__init__()` and `super().__init__()`.

**Improvement**: Convert all to Python 3 style `super().__init__()`.

**Files to modify**:
- [`pycycle/passthrough.py`](../../pycycle/passthrough.py:13)
- [`pycycle/mp_cycle.py`](../../pycycle/mp_cycle.py:205)
- Any other instances

**Depends on**: Nothing  
**Risk**: NONE

---

## Summary

| ID | Improvement | Priority | Risk | Phase |
|----|------------|----------|------|-------|
| S-01 | Consistent element hierarchy | MEDIUM | LOW | 1 |
| S-02 | Remove `setup.py` | LOW | LOW | 1 |
| S-03 | Remove `.travis.yml` | LOW | NONE | 1 |
| S-04 | Clean up deprecated code | MEDIUM | LOW | 1 |
| S-05 | MapData → dataclass | MEDIUM | MEDIUM | 2 |
| S-06 | Lazy-load pickle | MEDIUM | LOW | 1 |
| S-07 | High-level API | HIGH | LOW | 4 |
| S-08 | Template builders | MEDIUM | LOW | 4 |
| S-09 | FlowIn cleanup | LOW | LOW | 1 |
| S-10 | Standardise strings | LOW | NONE | 1 |
| S-11 | Standardise super() | LOW | NONE | 1 |
