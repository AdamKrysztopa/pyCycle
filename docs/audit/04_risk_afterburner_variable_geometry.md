# Risk 3: Absence of Afterburner & Variable Geometry

**Severity**: HIGH  
**Impact**: Cannot model supersonic military engines or mixed-flow turbofans with reheat

## Current State in pyCycle

### Combustor Element

[`Combustor`](../../pycycle/elements/combustor.py:19) is the closest existing element to an afterburner:

- Mixes fuel into incoming flow using [`ThermoAdd`](../../pycycle/thermo/thermo.py:190)
- Computes vitiated flow properties and fuel mass flow `Wfuel`
- Applies pressure loss via `PressureLoss` — reused from [`Duct`](../../pycycle/elements/duct.py)
- Supports design — Mach number input — and off-design — area input — modes
- Options: `fuel_type`, `statics`, `design`

**Key limitation**: The combustor is designed for the main burner position in the cycle. It assumes upstream flow is compressed air; it does not model:
- Flameholder aerodynamics
- Reheat-specific pressure losses — typically higher than main burner
- Variable fuel scheduling
- Smooth light-off/light-out transitions

### Nozzle Element

[`Nozzle`](../../pycycle/elements/nozzle.py) supports three configurations:
- `CV` — convergent only
- `CD` — convergent-divergent
- `CD_CV` — combined

The nozzle computes:
- Throat conditions from upstream total properties and pressure loss
- Exit static properties via Thermo calls
- Gross thrust `Fg`, velocity coefficient `Cv`, discharge coefficient `Cfg`

**Key limitations**:
- **No variable exit area** — area is computed from flow conditions, not specified as input
- **No area ratio control** — `A_exit / A_throat` is not a design variable
- **No coupling with afterburner state** — exit area cannot respond to AB on/off
- **Hard discrete switch** at choke boundary — see Risk 1

### Afterburning Turbojet Example

[`afterburning_turbojet.py`](../../example_cycles/afterburning_turbojet.py) demonstrates the workaround: it uses a **second `Combustor`** instance after the turbine to simulate an afterburner. This works but lacks:
- Smooth light-off transition
- Variable-geometry nozzle coupling
- Reheat-specific modelling — flameholder losses, stability limits

## Identified Issues

### 1. No Dedicated Afterburner Element

Users must manually wire a second combustor, configure it for post-turbine conditions, and set appropriate pressure losses. This is:
- Error-prone — wrong FAR limits, wrong pressure loss model
- Not physically representative — no flameholder, no stability limits
- Cannot model smooth AB light-off/out transitions

### 2. Fixed-Geometry Nozzle

The nozzle exit area is an **output**, not an input. This means:
- Cannot model variable-geometry C-D nozzles used on military engines
- Cannot implement area schedules — e.g., open nozzle for AB, close for dry thrust
- Cannot optimise nozzle geometry as a design variable

### 3. No AB-Nozzle Coupling

In real engines, afterburner activation requires nozzle area increase to maintain acceptable backpressure. There is no mechanism to:
- Link AB fuel flow to nozzle area
- Implement an area schedule as function of AB state
- Ensure smooth transitions in both fuel and geometry simultaneously

### 4. Discrete Transitions

The current combustor uses a step-function approach — FAR is either zero or the target value. Combined with the nozzle's discrete choke switch, this creates a doubly-discontinuous system that is very difficult for Newton solvers.

## What Is Missing

| Gap | Description | Priority |
|-----|-------------|----------|
| `Afterburner` element | Dedicated element with reheat-specific physics | HIGH |
| Variable-geometry nozzle | `A_exit` as input for C-D nozzles | HIGH |
| AB-nozzle coupling | Area schedule linked to AB state | MEDIUM |
| Smooth light-off model | Logistic ramp for AB fuel injection | MEDIUM |
| Reheat pressure loss model | Flameholder-specific dP/P correlation | LOW |

## Proposed Mitigations

### Afterburner Element

New file `pycycle/elements/afterburner.py` extending [`Element`](../../pycycle/element_base.py:9):

```
Afterburner
├── FlowIn - Fl_I
├── ThermoAdd - fuel mixing
├── PressureLoss - reheat-specific dP/P
├── Thermo(total_hP) - post-combustion properties
├── Thermo(static_MN | static_A) - exit statics
├── BalanceComp - FAR or T4 balance
└── SmoothLightoff - logistic ramp on effective FAR
```

Key features:
- `FAR_AB` input with `FAR_max` limit
- `AB_switch` input — 0.0 to 1.0 — controlling light-off via logistic function
- `dPqP_AB` — reheat-specific pressure loss, typically 5-10%
- `smooth_lightoff` option — default True — applies `FAR_eff = FAR_AB * sigmoid(kappa * (AB_switch - 0.5))`

### Variable-Geometry Nozzle Extension

Add `nozzType='variable_CD'` to [`Nozzle`](../../pycycle/elements/nozzle.py):

- Accept `A_exit` as an **input** — promoted to cycle level
- Compute exit static properties from specified area using `Thermo(mode='static_A')`
- Throat area remains computed from Mach = 1 conditions
- `A_exit / A_throat` becomes an explicit design variable or schedule output

### AB-Nozzle Coupling Schedule

Implement at cycle level via `om.ExecComp`:

```python
cycle.add_subsystem('nozzle_schedule', om.ExecComp(
    'A_exit = A_exit_base * (1 + A_factor * 0.5 * (1 + tanh(kappa * (AB_switch - 0.5))))',
    A_exit={'units': 'inch**2'},
    A_exit_base={'units': 'inch**2'}
))
```

This smoothly opens the nozzle as the afterburner activates.

## Validation Approach

1. **AB sanity tests** — turbojet with/without AB; verify thrust increase with AB on; check energy conservation
2. **Light-off smoothing** — ramp `AB_switch` from 0→1; verify smooth temperature and thrust curves
3. **Variable nozzle** — sweep `A_exit`; compare with analytic C-D nozzle equations
4. **Coupled AB-nozzle** — verify that AB activation + nozzle opening produces converged solutions across the transition

## Classification

| Mitigation | Type |
|-----------|------|
| Afterburner element | INTEGRATE — new element using existing patterns |
| Variable-geometry nozzle | PATCH — extend existing nozzle with new mode |
| AB-nozzle coupling | MITIGATE — cycle-level `ExecComp`, no element changes |
| Smooth light-off | INTEGRATE — part of afterburner element |
