# Improvement Plan: Maps System

**Related audit**: [Risk 2: Map Conventions & Scaling](../audit/03_risk_map_conventions.md)  
**Related PRs**: PR 3 — Map Loader & Unified Scaler

---

## MAP-01: Replace MapData with Typed Dataclasses

**Current state**: [`MapData`](../../pycycle/maps/map_data.py:3) is a bare `object()` subclass. Map data is attached as arbitrary attributes with no validation.

**Improvement**: Replace with validated dataclasses:

```python
from dataclasses import dataclass, field
import numpy as np

@dataclass
class CompressorMapData:
    """Validated compressor performance map."""
    alphaMap: np.ndarray          # IGV angle schedule
    NcMap: np.ndarray             # Corrected speed lines
    RlineMap: np.ndarray          # R-line operating points
    WcMap: np.ndarray             # Corrected flow: shape (alpha, Nc, Rline)
    effMap: np.ndarray            # Adiabatic efficiency: shape (alpha, Nc, Rline)
    PRmap: np.ndarray             # Pressure ratio: shape (alpha, Nc, Rline)
    defaults: dict = field(default_factory=dict)
    RlineStall: float = 1.0       # R-line value at surge

    def __post_init__(self):
        expected = (len(self.alphaMap), len(self.NcMap), len(self.RlineMap))
        for name in ['WcMap', 'effMap', 'PRmap']:
            arr = getattr(self, name)
            if arr.shape != expected:
                raise ValueError(
                    f'{name} shape {arr.shape} does not match '
                    f'expected {expected} from axis arrays'
                )

@dataclass  
class TurbineMapData:
    """Validated turbine performance map."""
    alphaMap: np.ndarray          # Variable geometry schedule
    NpMap: np.ndarray             # Corrected speed lines
    PRmap: np.ndarray             # Pressure ratio points
    WpMap: np.ndarray             # Corrected flow: shape (alpha, Np, PR)
    effMap: np.ndarray            # Adiabatic efficiency: shape (alpha, Np, PR)
    defaults: dict = field(default_factory=dict)

    def __post_init__(self):
        expected = (len(self.alphaMap), len(self.NpMap), len(self.PRmap))
        for name in ['WpMap', 'effMap']:
            arr = getattr(self, name)
            if arr.shape != expected:
                raise ValueError(
                    f'{name} shape {arr.shape} does not match '
                    f'expected {expected} from axis arrays'
                )
```

**Migration**: Existing map modules — `axi5.py`, `lpt2269.py`, etc. — would be updated to construct these dataclasses instead of `MapData()`:

```python
# Before
AXI5 = MapData()
AXI5.defaults = {'alphaMap': 0.0, ...}
AXI5.alphaMap = np.array([...])

# After
AXI5 = CompressorMapData(
    alphaMap=np.array([...]),
    NcMap=np.array([...]),
    RlineMap=np.array([...]),
    WcMap=np.array([...]),
    effMap=np.array([...]),
    PRmap=np.array([...]),
    defaults={'alphaMap': 0.0, 'NcMap': 1.0, 'PRmap': 5.2, 'RlineMap': 2.0},
    RlineStall=1.0
)
```

**Backwards compatibility**: Keep `MapData` as a deprecated alias that accepts the old pattern.

**Files to modify**:
- [`pycycle/maps/map_data.py`](../../pycycle/maps/map_data.py) — rewrite
- All 10 map files in `pycycle/maps/`
- [`pycycle/elements/compressor_map.py`](../../pycycle/elements/compressor_map.py) — accept new type
- [`pycycle/elements/turbine_map.py`](../../pycycle/elements/turbine_map.py) — accept new type
- N+3 map files in `example_cycles/N+3ref/`

**Depends on**: Nothing  
**Risk**: MEDIUM — touches many files but is straightforward

---

## MAP-02: Map Loader Utility

**Current state**: No way to load maps from external files. All maps are hard-coded in Python modules.

**Improvement**: New module `pycycle/map_utils.py` with loader functions:

```python
def load_compressor_map(file_path: str, format: str = 'csv') -> CompressorMapData:
    """
    Load a compressor map from an external file.
    
    CSV format expected columns:
    alpha, Nc, Rline, Wc, PR, eff
    
    NPSS format: structured text blocks.
    
    Parameters
    ----------
    file_path : str
        Path to the map data file
    format : str
        File format: 'csv', 'npss', 'json'
    
    Returns
    -------
    CompressorMapData
        Validated map data
    """

def load_turbine_map(file_path: str, format: str = 'csv') -> TurbineMapData:
    """Load a turbine map from an external file."""

def save_map(map_data, file_path: str, format: str = 'csv'):
    """Save a map to an external file for sharing/archiving."""
```

### CSV Format Convention

```csv
# Compressor Map: AXI5
# Axes: alpha, Nc, Rline
# Units: alpha=deg, Nc=frac, Rline=-, Wc=lbm/s, PR=-, eff=-
alpha,Nc,Rline,Wc,PR,eff
0.0,0.4,1.0,4.843,1.124,0.7357
0.0,0.4,1.2,5.191,1.115,0.7426
...
```

**Files to create**: `pycycle/map_utils.py`  
**Depends on**: MAP-01 — uses new dataclasses  
**Risk**: LOW — additive utility

---

## MAP-03: Surge Margin Computation

**Current state**: `RlineStall` is defined on some maps — e.g., [`axi5.py`](../../pycycle/maps/axi5.py:15) — but is **never used** in any calculation.

**Improvement**: Add `SurgeMarginCalc` component to compressor map:

```python
class SurgeMarginCalc(om.ExplicitComponent):
    """Compute surge margin from current operating point and surge line."""
    
    def initialize(self):
        self.options.declare('map_data', recordable=False)
    
    def setup(self):
        self.add_input('Wc', val=30.0, units='lbm/s', desc='Operating corrected flow')
        self.add_input('Nc', val=1.0, desc='Corrected speed')
        self.add_input('PR', val=5.0, desc='Operating pressure ratio')
        
        self.add_output('surge_margin', val=0.3, desc='Surge margin fraction')
        self.add_output('Wc_surge', val=20.0, units='lbm/s', desc='Flow at surge')
        self.add_output('PR_surge', val=6.0, desc='PR at surge')
    
    def compute(self, inputs, outputs):
        # Interpolate surge line at current Nc
        Wc_surge = interp(inputs['Nc'], map_data.NcMap, surge_line_Wc)
        PR_surge = interp(inputs['Nc'], map_data.NcMap, surge_line_PR)
        
        outputs['Wc_surge'] = Wc_surge
        outputs['PR_surge'] = PR_surge
        outputs['surge_margin'] = (inputs['Wc'] - Wc_surge) / Wc_surge
```

### Integration with CompressorMap

Add optional `compute_surge_margin` option:

```python
class CompressorMap(om.Group):
    def initialize(self):
        # ...existing...
        self.options.declare('compute_surge_margin', default=False)
    
    def setup(self):
        # ...existing map setup...
        if self.options['compute_surge_margin']:
            self.add_subsystem('surge', SurgeMarginCalc(map_data=...))
```

Expose `surge_margin` as a constrainable output for optimisation.

**Files to modify**: [`pycycle/elements/compressor_map.py`](../../pycycle/elements/compressor_map.py)  
**Files to create**: Add `SurgeMarginCalc` — in `compressor_map.py` or `map_utils.py`  
**Depends on**: MAP-01  
**Risk**: MEDIUM

---

## MAP-04: Extrapolation Controls

**Current state**: `MetaModelStructuredComp` is used with `extrapolate=True` in some maps. Operating outside map boundaries produces silently wrong results.

**Improvement**: Add extrapolation warning/clamping:

```python
class MapBoundsCheck(om.ExplicitComponent):
    """Check whether operating point is within map boundaries."""
    
    def setup(self):
        self.add_input('Nc', val=1.0)
        self.add_input('Rline', val=2.0)  # or PR for turbines
        self.add_output('in_bounds', val=1.0, desc='1.0 = in bounds, 0.0 = extrapolating')
        self.add_output('Nc_clipped', val=1.0)
        self.add_output('Rline_clipped', val=2.0)
    
    def compute(self, inputs, outputs):
        Nc = inputs['Nc']
        Nc_min, Nc_max = self.options['Nc_range']
        outputs['Nc_clipped'] = np.clip(Nc, Nc_min, Nc_max)
        in_bounds = (Nc_min <= Nc <= Nc_max) and ...
        outputs['in_bounds'] = float(in_bounds)
```

Also add a cycle-level diagnostic that reports which maps are extrapolating after a converged solution.

**Files to modify**: [`pycycle/elements/compressor_map.py`](../../pycycle/elements/compressor_map.py), [`pycycle/elements/turbine_map.py`](../../pycycle/elements/turbine_map.py)  
**Depends on**: Nothing  
**Risk**: LOW

---

## MAP-05: Unified MapScaler

**Current state**: Compressor and turbine maps use slightly different scaling conventions. `MapScalars` computes `s_PR = (PR_des - 1) / (PRmap_des - 1)` for compressors. Turbines may use different conventions.

**Improvement**: Refactor into a single `MapScaler` class that handles both:

```python
class MapScaler:
    """Unified scaling logic for both compressor and turbine maps."""
    
    @staticmethod
    def compute_scalars(design_values: dict, map_defaults: dict, 
                        map_type: str = 'compressor') -> dict:
        """
        Compute scaling factors from design values and map defaults.
        
        Returns dict with s_PR, s_Wc/s_Wp, s_Nc/s_Np, s_eff
        """
```

Document the differences:
- Compressor: `s_PR = (PR_des - 1) / (PRmap_des - 1)` — PR relative to 1
- Turbine: `s_PR = PR_des / PRmap_des` — PR is expansion ratio
- Both: `s_eff = eff_des / eff_map_des`, `s_Wc = Wc_des / Wc_map_des`

**Files to modify**: [`pycycle/elements/compressor_map.py`](../../pycycle/elements/compressor_map.py), [`pycycle/elements/turbine_map.py`](../../pycycle/elements/turbine_map.py)  
**Depends on**: Nothing  
**Risk**: MEDIUM

---

## MAP-06: Map Documentation

**Current state**: No documentation of map conventions, axis ordering, or units.

**Improvement**: Create documentation covering:

1. **Axis ordering** — alpha × Nc × Rline for compressors; alpha × Np × PR for turbines
2. **Units** — all maps use fractional corrected speed, lbm/s for flow, dimensionless PR and eff
3. **Scaling rules** — how `MapScalars` transforms between design and map coordinate systems
4. **Adding custom maps** — step-by-step guide with CSV loading
5. **Map quality checks** — monotonicity, coverage, interpolation smoothness

**Files to create**: `docs/improvement_plan/` already covers this; also update `pycycle/docs/reference_guide/maps/index.rst`  
**Depends on**: MAP-01, MAP-02  
**Risk**: NONE

---

## Summary

| ID | Improvement | Priority | Risk | Phase |
|----|------------|----------|------|-------|
| MAP-01 | Typed MapData dataclasses | HIGH | MEDIUM | 2 |
| MAP-02 | Map loader utility | HIGH | LOW | 2 |
| MAP-03 | Surge margin computation | HIGH | MEDIUM | 2 |
| MAP-04 | Extrapolation controls | MEDIUM | LOW | 2 |
| MAP-05 | Unified MapScaler | MEDIUM | MEDIUM | 2 |
| MAP-06 | Map documentation | MEDIUM | NONE | 2 |
