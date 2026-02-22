# Risk 5: Unit Consistency & International Use

**Severity**: MEDIUM  
**Impact**: Mixed imperial/SI defaults confuse international users; hard-coded unit assumptions create subtle bugs

## Current State in pyCycle

### Unit Annotations

Every input and output specifies units via OpenMDAO's unit system:

| Component | Variable | Units | System |
|-----------|----------|-------|--------|
| [`FlowIn`](../../pycycle/flow_in.py:24) | `tot:T` | `degR` | Imperial |
| [`FlowIn`](../../pycycle/flow_in.py:26) | `tot:P` | `lbf/inch**2` | Imperial |
| [`FlowIn`](../../pycycle/flow_in.py:52) | `stat:W` | `lbm/s` | Imperial |
| [`PsResid`](../../pycycle/thermo/static_ps_resid.py:17) | `Ts` | `degK` | SI |
| [`PsResid`](../../pycycle/thermo/static_ps_resid.py:18) | `ht` | `J/kg` | SI |
| [`PsResid`](../../pycycle/thermo/static_ps_resid.py:30) | `Ps` | `bar` | SI |
| [`tabular_thermo.py`](../../pycycle/thermo/tabular/tabular_thermo.py:33) | `P` | `Pa` | SI |
| [`tabular_thermo.py`](../../pycycle/thermo/tabular/tabular_thermo.py:34) | `T` | `degK` | SI |
| [`EngUnitProps`](../../pycycle/thermo/unit_comps.py:56) | `T` | `degR` | Imperial |
| [`EngUnitProps`](../../pycycle/thermo/unit_comps.py:57) | `P` | `lbf/inch**2` | Imperial |

OpenMDAO handles conversions automatically when variables are connected, but the inconsistency creates confusion about what units a given component expects.

### Constants and Conversion Factors

[`constants.py`](../../pycycle/constants.py) defines:

```python
BTU_s2HP = 1.4148532                    # Imperial conversion
HP_per_RPM_to_FT_LBF = 5252.11         # Imperial conversion
R_UNIVERSAL_SI = 8314.4598              # SI
R_UNIVERSAL_ENG = 1.9872035             # Imperial
g_c = 32.174                            # lbm·ft/(lbf·s²) - gravitational constant
T_STDeng = 518.67                       # degR - standard temperature
P_STDeng = 14.695951                    # psi - standard pressure
P_REF = 1.01325                         # atm → bar
```

These are used directly in compute functions:

- [`CorrectedInputsCalc`](../../pycycle/elements/compressor.py:37) divides by `P_STDeng` and `T_STDeng` — assumes imperial inputs
- [`Shaft`](../../pycycle/elements/shaft.py:32) uses `2 * pi / 60 / 550` — hardcoded HP↔ft·lbf/s conversion
- Nozzle thrust uses `g_c` for force unit conversion

### EngUnit Conversion Components

[`EngUnitProps`](../../pycycle/thermo/unit_comps.py:51) and [`EngUnitStaticProps`](../../pycycle/thermo/unit_comps.py) are passthrough components that convert internal SI-ish thermo properties to imperial units for the flow station outputs. Their name — "Eng" for English — reveals the imperial-first design.

## Identified Issues

### 1. Mixed Unit Systems Across Layers

The codebase has three distinct unit layers:
1. **User-facing flow stations** — imperial — degR, psi, lbm/s, Btu/lbm
2. **Internal thermo calculations** — SI — degK, Pa, J/kg
3. **Element compute functions** — mixed — uses whichever is convenient

This creates a confusing mental model where the same physical quantity — e.g., temperature — exists in different units at different points in the same element.

### 2. Hard-Coded Imperial Constants in Compute Functions

Corrected flow calculations in [`compressor.py`](../../pycycle/elements/compressor.py:39) use:

```python
self.delta = inputs['Pt'] / P_STDeng  # P_STDeng = 14.695951 psi
self.theta = inputs['Tt'] / T_STDeng  # T_STDeng = 518.67 degR
```

These assume inputs are in psi and degR. If a user connects a source with Pa units, OpenMDAO converts — but the hard-coded reference values only make sense in one unit system.

### 3. `g_c` Usage Creates Confusion

The gravitational constant `g_c = 32.174` is used in force/momentum calculations — e.g., nozzle thrust. In SI units, `g_c = 1.0` by definition. The explicit use of `g_c` is:
- Confusing for SI-trained engineers
- Error-prone if someone forgets to include it
- Unnecessary if units are handled properly by OpenMDAO

### 4. No `unit_system` Option

There is no way for users to say "I want everything in SI" or "I want everything in Imperial". Every element independently chooses its default units.

### 5. EngUnitProps Naming

The name "EngUnitProps" — English Unit Properties — is hardcoded. If a user wants SI outputs, they cannot easily change the flow station output units without modifying the library.

## What Is Missing

| Gap | Description | Priority |
|-----|-------------|----------|
| `unit_system` option | Cycle-level setting — `ENG` or `SI` | MEDIUM |
| SI-compatible flow stations | Flow station outputs in user's chosen unit system | MEDIUM |
| Replace `g_c` usage | Use OpenMDAO unit conversions instead | LOW |
| Centralised unit utilities | `to_SI()` / `from_SI()` helper functions | LOW |
| Unit documentation | Table of all variables and their units | LOW |

## Proposed Mitigations

### Unit System Option

Add to [`Cycle`](../../pycycle/mp_cycle.py:13) and [`Element`](../../pycycle/element_base.py:9):

```python
self.options.declare('unit_system', default='ENG', values=['ENG', 'SI'],
    desc='Unit system for default values and flow station outputs')
```

When `unit_system='SI'`:
- Flow station outputs use degK, Pa, kg/s, J/kg
- `EngUnitProps` → `SIUnitProps` — or a generic `UnitProps` that respects the setting
- Default values adjusted accordingly

### Deprecate `g_c`

Replace explicit `g_c` usage with proper OpenMDAO unit declarations:

```python
# Before
self.add_output('Fg', units='lbf')
Fg = W * V / g_c

# After
self.add_output('Fg', units='N')  # or 'lbf' with proper unit handling
Fg = W * V  # units handle conversion
```

### Centralised Unit Utilities

New module `pycycle/unit_utils.py`:

```python
UNIT_SYSTEMS = {
    'ENG': {'T': 'degR', 'P': 'lbf/inch**2', 'W': 'lbm/s', 'h': 'Btu/lbm', ...},
    'SI':  {'T': 'degK', 'P': 'Pa', 'W': 'kg/s', 'h': 'J/kg', ...}
}

def get_unit(var_type: str, system: str = 'ENG') -> str:
    return UNIT_SYSTEMS[system][var_type]
```

## Validation Approach

1. **Unit round-trip tests** — convert known inputs to SI, run element, convert back; verify match with imperial run
2. **Full cycle in SI** — build turbofan with `unit_system='SI'`; compare thrust/fuel flow with converted imperial result
3. **Derivative checks** — verify `check_partials()` passes in both unit systems
4. **Backwards compatibility** — default `unit_system='ENG'` must produce identical results to current code

## Classification

| Mitigation | Type |
|-----------|------|
| `unit_system` option | INTEGRATE — modifies `Cycle`/`Element` architecture |
| `UnitProps` replacement | PATCH — refactors existing passthrough components |
| `g_c` deprecation | PATCH — small changes in compute functions |
| Conversion utilities | PATCH — new utility module |
| Documentation | MITIGATE — no code changes |
