# Risk 2: Map Conventions & Scaling

**Severity**: HIGH  
**Impact**: Error-prone vendor map integration, no surge margin enforcement, inconsistent scaling

## Current State in pyCycle

### Map Data Storage

Maps are stored as Python modules containing numpy arrays on a [`MapData`](../../pycycle/maps/map_data.py:3) container — a bare `object` subclass with **4 lines of code**:

```python
# stupid hack so I can create data containers in python
class MapData(object):
    pass
```

Each map file — e.g., [`axi5.py`](../../pycycle/maps/axi5.py) — creates a `MapData()` instance and attaches arrays as attributes:

```python
AXI5 = MapData()
AXI5.defaults = {'alphaMap': 0.0, 'NcMap': 1.00, 'PRmap': 5.2, 'RlineMap': 2.0}
AXI5.RlineStall = 1.0
AXI5.alphaMap = np.array([...])
AXI5.NcMap = np.array([...])
AXI5.RlineMap = np.array([...])
AXI5.WcMap = np.array([...])   # 3D: alpha x Nc x Rline
AXI5.effMap = np.array([...])  # 3D: alpha x Nc x Rline
AXI5.PRmap = np.array([...])   # 3D: alpha x Nc x Rline
```

### Map Interpolation

[`CompressorMap`](../../pycycle/elements/compressor_map.py) and [`TurbineMap`](../../pycycle/elements/turbine_map.py) use OpenMDAO's `MetaModelStructuredComp` for N-D interpolation. The pattern:

- **Design mode**: User specifies `PR`, `eff`, `Nc` → map computes scalars `s_PR`, `s_eff`, `s_Wc`, `s_Nc`
- **Off-design mode**: Scalars from design are inputs → map lookups produce `PR`, `eff`, `Wc` via `ScaledMapValues`
- **Balance**: A `BalanceComp` adjusts `NpMap`/`NcMap` and `PRmap`/`RlineMap` to match corrected flow and speed

### Scaling Components

- `MapScalars` — computes `s_PR = (PR_des - 1) / (PRmap_des - 1)` and similar for `Wc`, `Nc`, `eff`
- `ScaledMapValues` — applies scalars to map outputs: `PR = s_PR * (PRmap - 1) + 1`

## Identified Issues

### 1. No Standardised Map Ingestion

Users must manually create `MapData` objects with correctly shaped numpy arrays. There is:
- No loader for common formats — CSV, Excel, NPSS map format
- No validation of array shapes or dimension consistency
- No unit conversion when importing vendor data
- No documentation of required array conventions — axes order, normalisation

### 2. No Surge Margin Computation

Maps contain `RlineStall` as a static attribute but:
- No component computes actual surge margin during operation
- No mechanism to constrain operating point away from surge
- No warning when approaching or crossing the surge line
- `RlineStall` is defined on some maps but never used in calculations

### 3. Manual Scaling Is Error-Prone

Scaling factors are computed in `MapScalars` but:
- Users must provide correct design-point map values in `map_data.defaults`
- If defaults don't match the actual map data, scaling produces wrong results
- No bounds checking on scalars — unrealistic extrapolation can occur
- Compressor and turbine maps use slightly different scaling conventions

### 4. No Map Extrapolation Control

`MetaModelStructuredComp` has `extrapolate=True` by default in some maps. This means:
- Operating far from map boundaries produces silently wrong results
- No warning or error when extrapolating beyond map coverage
- No option to clamp outputs at map boundaries

### 5. Inconsistent Map Coordinate Systems

Compressor maps use corrected flow `Wc` and corrected speed `Nc` with standard-day corrections:

```python
# compressor.py:43
outputs['Wc'] = W * theta**0.5 / delta
outputs['Nc'] = Nmech * theta**-0.5
```

Turbine maps use `Wp` and `Np` without standard-day normalisation:

```python
# turbine.py:40
outputs['Wp'] = W_in * Tt**0.5 / Pt
outputs['Np'] = Nmech * Tt**-0.5
```

This difference is physically correct — turbines use raw corrected parameters — but is poorly documented and can confuse users integrating new maps.

### 6. Hardcoded Map Defaults in Elements

[`Compressor`](../../pycycle/elements/compressor.py) defaults to `NCP01` map; [`Turbine`](../../pycycle/elements/turbine.py) defaults to `LPT2269`. These defaults are set in element `__init__` and may not match the user's application.

## What Is Missing

| Gap | Description | Priority |
|-----|-------------|----------|
| `MapLoader` | Utility to load maps from CSV/NPSS format with validation | HIGH |
| `SurgeMargin` component | Compute and expose surge margin as output | HIGH |
| Map validation | Check array shapes, bounds, monotonicity | MEDIUM |
| Unified `MapScaler` | Single scaling class for both compressor and turbine | MEDIUM |
| Extrapolation controls | Configurable clamping or error on extrapolation | MEDIUM |
| Map documentation | Conventions, axis ordering, units, scaling rules | MEDIUM |

## Proposed Mitigations

### Standardised Map Loader

New module `pycycle/map_utils.py`:

```python
def load_map(file_path: str, map_type: str = 'compressor', unit_system: str = 'ENG') -> MapData:
    """Load a performance map from CSV/NPSS format.
    
    Expected CSV columns:
    - Compressor: alpha, Nc, Rline, Wc, PR, eff
    - Turbine: alpha, Np, PR, Wp, eff
    
    Validates array shapes, monotonicity of speed lines, and unit consistency.
    """
```

### Surge Margin Component

Add `SurgeMarginCalc` to compressor/turbine map modules:

```python
class SurgeMarginCalc(om.ExplicitComponent):
    """Compute surge margin from operating point and surge line."""
    # Inputs: Wc_operating, Nc, RlineStall data
    # Output: surge_margin = (Wc_operating - Wc_surge) / Wc_surge
```

Expose as an output that can be constrained in optimisation: `surge_margin >= 0.1`

### Map Validation

Add validation in `MapData` — or replace it with a proper dataclass:

```python
@dataclass
class CompressorMapData:
    alphaMap: np.ndarray
    NcMap: np.ndarray
    RlineMap: np.ndarray
    WcMap: np.ndarray  # shape: (len(alpha), len(Nc), len(Rline))
    effMap: np.ndarray
    PRmap: np.ndarray
    defaults: dict
    RlineStall: float = 1.0
    
    def __post_init__(self):
        expected_shape = (len(self.alphaMap), len(self.NcMap), len(self.RlineMap))
        for name in ['WcMap', 'effMap', 'PRmap']:
            arr = getattr(self, name)
            assert arr.shape == expected_shape, f"{name} shape {arr.shape} != {expected_shape}"
```

## Validation Approach

1. **Loader tests** — sample CSV files with known values; verify shapes and unit conversions
2. **Scaling regression** — compute scalars manually for `LPT2269` and compare with `MapScaler` output
3. **Surge margin tests** — operating points above, on, and below surge line; verify sign of `surge_margin`
4. **Extrapolation tests** — verify warnings/errors when operating beyond map boundaries

## Classification

| Mitigation | Type |
|-----------|------|
| `MapLoader` + validation | INTEGRATE — extends existing map infrastructure |
| `SurgeMarginCalc` | INTEGRATE — adds physical realism to maps |
| Unified `MapScaler` | PATCH — refactors existing code |
| Documentation | MITIGATE — no code changes |
