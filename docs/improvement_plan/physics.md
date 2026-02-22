# Improvement Plan: Physics Models

**Related audit**: [Risk 1](../audit/02_risk_convergence_solver.md), [Risk 3](../audit/04_risk_afterburner_variable_geometry.md), [Risk 4](../audit/05_risk_cooling_bleed.md)  
**Related PRs**: PR 1, PR 4, PR 5, PR 6, PR 7

---

## PHY-01: Nozzle Logistic Blending at Choke Boundary

**Current state**: The nozzle uses a hard `if/else` to select between static-pressure-based and Mach-number-based solutions at the choking boundary. This creates a non-differentiable discontinuity.

**Improvement**: Replace the discrete switch with a logistic blending function:

```python
# In nozzle.py — throat/exit static property selection
def _smooth_choke_blend(self, Ps_calc, Ps_choked, kappa=50.0):
    """Smooth blending between choked and unchoked states."""
    deltaP = (Ps_calc - Ps_choked) / max(Ps_choked, 1e-10)
    alpha = 0.5 * (1.0 + np.tanh(kappa * deltaP))
    return alpha  # 0 = fully choked, 1 = fully unchoked
```

Add configurable `kappa` parameter:
```python
self.options.declare('choke_blend_kappa', default=50.0,
    desc='Sharpness of logistic blending at choke boundary. Higher = sharper transition.')
```

**Files to modify**: [`pycycle/elements/nozzle.py`](../../pycycle/elements/nozzle.py)  
**Depends on**: Nothing  
**Risk**: LOW — localised, preserves physics at kappa→∞

**Validation**:
- `check_partials()` at choke boundary — should pass with smooth blend
- Throttle sweep crossing choke — monotonic thrust curve
- Comparison with large kappa — should match existing discrete behaviour

---

## PHY-02: Afterburner Element

**Current state**: Users model afterburners by placing a second [`Combustor`](../../pycycle/elements/combustor.py) after the turbine — see [`afterburning_turbojet.py`](../../example_cycles/afterburning_turbojet.py). This lacks reheat-specific physics.

**Improvement**: New element `pycycle/elements/afterburner.py`:

### Element Architecture

```
Afterburner(Element)
├── FlowIn('Fl_I') — hot gas from turbine
├── SmoothLightoff — logistic ramp on effective FAR
│   inputs:  FAR_AB, AB_switch
│   outputs: FAR_effective
├── ThermoAdd — mix fuel into flow
│   inputs:  Fl_I composition, FAR_effective
│   outputs: mixed composition
├── PressureLoss — reheat-specific dP/P
│   inputs:  Pt_in, dPqP_AB
│   outputs: Pt_out
├── Thermo(total_hP) — post-combustion total properties
├── Thermo(static_MN | static_A) — exit static properties
├── PassThrough(W) — mass flow with fuel addition
└── Outputs: Fl_O, Wfuel_AB
```

### Key Options

```python
class Afterburner(Element):
    def initialize(self):
        super().initialize()
        self.options.declare('fuel_type', default='Jet-A(g)')
        self.options.declare('statics', default=True)
        self.options.declare('FAR_max', default=0.05,
            desc='Maximum allowed afterburner fuel-air ratio')
        self.options.declare('smooth_lightoff', default=True,
            desc='Use logistic ramp for smooth AB activation')
        self.options.declare('lightoff_kappa', default=20.0,
            desc='Sharpness of light-off transition')
        self.options.declare('dPqP_default', default=0.05,
            desc='Default reheat pressure loss fraction')
```

### Smooth Light-Off

```python
class SmoothLightoff(om.ExplicitComponent):
    """Apply logistic ramp to afterburner fuel-air ratio."""
    
    def setup(self):
        self.add_input('FAR_AB', val=0.0, desc='Target AB fuel-air ratio')
        self.add_input('AB_switch', val=0.0, desc='AB activation: 0=off, 1=full')
        self.add_output('FAR_effective', val=0.0, desc='Smoothed effective FAR')
    
    def compute(self, inputs, outputs):
        kappa = self.options['kappa']
        outputs['FAR_effective'] = inputs['FAR_AB'] * 0.5 * (
            1.0 + np.tanh(kappa * (inputs['AB_switch'] - 0.5))
        )
```

**Files to create**: `pycycle/elements/afterburner.py`, `pycycle/elements/test/test_afterburner.py`  
**Files to modify**: [`pycycle/api.py`](../../pycycle/api.py) — export  
**Depends on**: PHY-01 — nozzle smoothing pattern  
**Risk**: MEDIUM

---

## PHY-03: Variable-Geometry Nozzle

**Current state**: [`Nozzle`](../../pycycle/elements/nozzle.py) computes exit area as an output. No `A_exit` input exists.

**Improvement**: Add `nozzType='variable_CD'`:

```python
# In Nozzle.initialize()
self.options.declare('nozzType', default='CV',
    values=['CV', 'CD', 'CD_CV', 'variable_CD'],
    desc='Nozzle type')
```

When `nozzType='variable_CD'`:
1. Accept `A_exit` as an **input** — units `inch**2` or `m**2`
2. Compute throat from Mach=1 conditions — same as current CD
3. Compute exit static properties from specified area via `Thermo(mode='static_A')`
4. Output `A_ratio = A_exit / A_throat` as diagnostic
5. Still output `Fg`, `V_exit`, `Ps_exit`

### AB-Nozzle Coupling

Provide a utility or example for coupling:

```python
# At cycle level
cycle.add_subsystem('nozzle_schedule', om.ExecComp(
    'A_exit = A_base * (1.0 + A_factor * 0.5 * (1.0 + tanh(kappa * (AB_sw - 0.5))))',
    A_exit={'units': 'inch**2'},
    A_base={'units': 'inch**2'},
    A_factor={'val': 0.5},
    kappa={'val': 20.0},
    AB_sw={'val': 0.0}
))
cycle.connect('afterburner.AB_switch', 'nozzle_schedule.AB_sw')
cycle.connect('nozzle_schedule.A_exit', 'nozz.A_exit')
```

**Files to modify**: [`pycycle/elements/nozzle.py`](../../pycycle/elements/nozzle.py)  
**Depends on**: PHY-01, PHY-02  
**Risk**: LOW — additive option, doesn't change existing modes

---

## PHY-04: Cooling-Integrated Turbine

**Current state**: [`TurbineCooling`](../../pycycle/elements/cooling.py) and [`CombineCooling`](../../pycycle/elements/cooling.py) exist as standalone components. They are not integrated into [`Turbine`](../../pycycle/elements/turbine.py) — requiring ~50 lines of manual wiring per cooling row.

**Improvement**: Add `cooling_rows` option to `Turbine`:

```python
class Turbine(Element):
    def initialize(self):
        super().initialize()
        # ... existing options ...
        self.options.declare('cooling_rows', default=None, types=(list, type(None)),
            desc='List of cooling row configurations')
```

Each cooling row config:
```python
{
    'name': 'row1',           # Internal name
    'bleed_port': 'cool_1',   # Name of bleed flow input port
    'x_factor': 0.9,          # Cooling effectiveness factor
    'T_metal': 2460.0,        # Metal temperature limit (degR)
}
```

For each row in `setup()`:
1. Add `FlowIn` for cooling port
2. Add `CoolingCalcs` subsystem — connect gas and cooling properties
3. Add `ThermoAdd(mix_mode='flow')` — mix cooling into primary
4. Adjust enthalpy for work extraction between rows

Expose outputs:
- `W_cool_row{i}` — cooling mass flow per row
- `Pt_stage{i}` — total pressure at each stage
- `Tt_stage{i}` — total temperature at each stage
- `W_cool_total` — total cooling mass flow

**Files to modify**: [`pycycle/elements/turbine.py`](../../pycycle/elements/turbine.py)  
**Files to modify**: [`pycycle/elements/cooling.py`](../../pycycle/elements/cooling.py) — ensure compatibility  
**Depends on**: Nothing — uses existing cooling components  
**Risk**: HIGH — modifies core turbine element

---

## PHY-05: Bleed Reinjection Element

**Current state**: [`BleedOut`](../../pycycle/elements/bleed_out.py) removes flow but there is no standard element to reinject bleed or cooling air.

**Improvement**: New element `pycycle/elements/bleed_reinject.py`:

```
BleedReinject(Element)
├── FlowIn('Fl_main') — primary flow
├── FlowIn('Fl_bleed_0') ... FlowIn('Fl_bleed_N') — bleed inputs
├── MassFlowSum — W_out = W_main + sum(W_bleed_i)
├── EnthalpyMix — h_out = (W_main*h_main + sum(W_i*h_i)) / W_out
├── ThermoAdd(mix_mode='flow') — composition mixing
├── Thermo(total_hP) — mixed total properties
├── Thermo(static_Ps | static_A | static_MN) — mixed statics
└── Outputs: Fl_O
```

### Options
```python
class BleedReinject(Element):
    def initialize(self):
        super().initialize()
        self.options.declare('bleed_names', types=(list, tuple),
            desc='Names of bleed flow input ports')
        self.options.declare('statics', default=True)
```

### Design vs Off-Design
- **Design**: User specifies MN at exit → static from Mach
- **Off-Design**: Area from design transferred → static from area

**Files to create**: `pycycle/elements/bleed_reinject.py`, `pycycle/elements/test/test_bleed_reinject.py`  
**Files to modify**: [`pycycle/api.py`](../../pycycle/api.py) — export  
**Depends on**: Nothing — uses existing ThermoAdd  
**Risk**: MEDIUM

---

## PHY-06: Mass Conservation Validation

**Current state**: No automated check that mass flow is conserved through the cycle.

**Improvement**: Add validation method to [`Cycle`](../../pycycle/mp_cycle.py:13):

```python
def validate_mass_conservation(self, tol=1e-6):
    """
    Check mass flow conservation at all junction points.
    
    For each element with both input and output flow:
    - W_out should equal W_in (± bleeds, fuel addition)
    - Report any violations exceeding tolerance
    """
```

Call automatically in `configure()` or provide as a diagnostic utility.

**Files to modify**: [`pycycle/mp_cycle.py`](../../pycycle/mp_cycle.py)  
**Depends on**: Nothing  
**Risk**: LOW — diagnostic only

---

## PHY-07: Resolve `n_moles` Issue in CEA

**Current state**: The TODO in [`chem_eq.py`](../../pycycle/thermo/cea/chem_eq.py:215):
> "hack to handle the fact that n_moles doesn't get set if you only call apply_linear"

And the TODO in [`thermo.py`](../../pycycle/thermo/thermo.py:57):
> "remove 'n', 'n_moles' variable from flow station"

These indicate a known issue where `n_moles` is not properly initialised in certain solver paths.

**Improvement**:
1. Investigate the `n_moles` initialisation path — when `apply_linear` is called without `apply_nonlinear`
2. Either ensure `n_moles` is always properly set — via `guess_nonlinear` or `solve_nonlinear`
3. Or refactor to remove `n_moles` from the flow station — as the TODO suggests

**Files to modify**: [`pycycle/thermo/cea/chem_eq.py`](../../pycycle/thermo/cea/chem_eq.py)  
**Depends on**: Nothing  
**Risk**: HIGH — CEA correctness issue

---

## PHY-08: Flow Station Variable Reorganisation

**Current state**: The TODO in [`flow_in.py`](../../pycycle/flow_in.py:46):
> "takes these out of static (keep them top level)"

Variables `V`, `Vsonic`, `MN`, `area`, `Wc`, `W` are currently under `stat:` namespace but are arguably top-level flow quantities.

**Improvement**: Move flow-level variables out of `stat:` namespace:

```python
# Current: flow:stat:V, flow:stat:MN, flow:stat:W
# Proposed: flow:V, flow:MN, flow:W
```

This is a **breaking change** that would require updating all flow connections. Should be done with a deprecation period.

**Files to modify**: [`pycycle/flow_in.py`](../../pycycle/flow_in.py), [`pycycle/mp_cycle.py`](../../pycycle/mp_cycle.py), all elements  
**Depends on**: Nothing  
**Risk**: HIGH — breaking change

---

## Summary

| ID | Improvement | Priority | Risk | Phase |
|----|------------|----------|------|-------|
| PHY-01 | Nozzle logistic blending | HIGH | LOW | 1 |
| PHY-02 | Afterburner element | HIGH | MEDIUM | 2 |
| PHY-03 | Variable-geometry nozzle | HIGH | LOW | 2 |
| PHY-04 | Cooling-integrated turbine | HIGH | HIGH | 3 |
| PHY-05 | Bleed reinjection element | MEDIUM | MEDIUM | 3 |
| PHY-06 | Mass conservation validation | MEDIUM | LOW | 1 |
| PHY-07 | Resolve n_moles issue | HIGH | HIGH | 1 |
| PHY-08 | Flow station reorganisation | LOW | HIGH | 4 |
