# Risk 4: Cooling & Bleed Integration

**Severity**: HIGH  
**Impact**: Turbine cooling not integrated into turbine element; bleed reinjection requires manual wiring

## Current State in pyCycle

### BleedOut Element

[`BleedOut`](../../pycycle/elements/bleed_out.py) removes fractions of the incoming mass flow and produces separate bleed ports:

- Uses `BleedCalcs` to compute bleed mass flows from user-specified fractions
- Passes enthalpy and composition through `Thermo` calls for the remaining flow
- Static properties computed via `Thermo(mode='static_MN')` or `Thermo(mode='static_A')`
- Supports multiple named bleed ports — e.g., `bld_inlet`, `bld_exit`
- Each bleed port produces a separate flow station with full thermodynamic properties

**Key observation**: `BleedOut` only **removes** flow. There is no corresponding element to **reinject** bleed flow back into the main stream.

### Cooling Calculations

[`cooling.py`](../../pycycle/elements/cooling.py) contains two components:

1. **`TurbineCooling`** — `om.Group` that computes required cooling flow based on:
   - Turbine gas temperature and metal temperature limits
   - Technology factors — `x_factor` for cooling effectiveness
   - Incoming bleed flow properties
   - Outputs: `W_cool` — required cooling mass flow

2. **`CombineCooling`** — combines multiple cooling flow sources into a single stream

**Key limitation**: These components are **standalone** — they are not called from inside the [`Turbine`](../../pycycle/elements/turbine.py) element. Users must:
1. Manually instantiate `TurbineCooling` as a separate subsystem
2. Connect turbine gas properties to cooling inputs
3. Connect bleed source properties to cooling inputs
4. Connect cooling outputs back to the turbine or downstream components
5. Account for mass flow changes in shaft power calculations

This manual wiring is demonstrated in the N+3 reference examples but is complex and error-prone.

### Turbine Element

[`Turbine`](../../pycycle/elements/turbine.py) models a single-stage or lumped turbine:

- Corrected inputs — `Wp`, `Np` — via `CorrectedInputsCalc`
- Pressure drop and work extraction
- Polytropic efficiency via `eff_poly_calc`
- Optional bleed ports — `bleed_names` option adds `FlowIn` ports for each bleed
- Map-based off-design via `TurbineMap`

**Key limitation**: The turbine **does not account for cooling flows** internally:
- No cooling mass flow injection between blade rows
- No mixing of cooling air with hot gas
- No adjustment of work extraction for cooling penalty
- Bleed ports accept flow but do not model the cooling physics

### N+3 Reference Example Pattern

The [`N3ref.py`](../../example_cycles/N+3ref/N3ref.py) example demonstrates the current manual approach:

```python
# Manual cooling setup - requires ~50 lines of boilerplate per cooling row
cycle.add_subsystem('hpt_cooling', pyc.TurbineCooling(...))
cycle.connect('hpt.Fl_O:tot:T', 'hpt_cooling.Tt_gas')
cycle.connect('bld3.bld_inlet.Fl_O:tot:T', 'hpt_cooling.Tt_cool')
# ... many more connections
```

## Identified Issues

### 1. No Integrated Cooling in Turbine

Cooling flows are modelled outside the turbine, requiring 10-20 manual connections per cooling row. This means:
- Easy to make connection errors
- Difficult to model multi-row cooling — stator 1, rotor 1, stator 2, etc.
- No automatic adjustment of turbine work for cooling penalty
- No standard pattern — each user implements differently

### 2. No Bleed Reinjection Element

When cooling air or bleed air needs to be mixed back into the main flow — e.g., after a turbine row or before a mixer — users must manually create `ThermoAdd` instances and connect all flow properties. There is no standard `BleedReinject` element.

### 3. Incomplete Cooling Test Coverage

[`test_cooling.py`](../../pycycle/elements/test/test_cooling.py:139) has commented-out assertions:

```python
assert_near_equal(p['W_cool'], 4.44635, tol)
# assert_near_equal(self, p['Pt_out'], 4.44635, tol) # TODO: set this
# assert_near_equal(self, p['ht_out'], 4.44635, tol)
```

Pressure and enthalpy outputs are not validated — significant gap in test coverage.

### 4. No Mass Conservation Checks

There is no automated check that bleed extraction + cooling injection conserves mass flow through the cycle. Users must manually verify that `W_out = W_in - W_bleed + W_cool_reinject`.

## What Is Missing

| Gap | Description | Priority |
|-----|-------------|----------|
| Cooling-integrated turbine | `cooling_rows` option on Turbine element | HIGH |
| `BleedReinject` element | Standard element for mixing bleed/cooling back | HIGH |
| Mass conservation checks | Automated validation in `Cycle.configure()` | MEDIUM |
| Multi-row cooling model | Per-row cooling with inter-row mixing | MEDIUM |
| Cooling test coverage | Complete assertions in `test_cooling.py` | MEDIUM |
| Standard bleed naming | Convention for `bld_*` and `cool_row*` ports | LOW |

## Proposed Mitigations

### Cooling-Enabled Turbine

Extend [`Turbine`](../../pycycle/elements/turbine.py) with `cooling_rows` option:

```python
class Turbine(Element):
    def initialize(self):
        # ... existing options ...
        self.options.declare('cooling_rows', default=None,
            desc='List of cooling row configs: [{name, bleed_port, x_factor, T_metal}]')
```

For each cooling row:
1. Create `CoolingCalcs` subsystem inside the turbine
2. Connect primary flow properties — `Tt`, `Pt`, `ht` — to cooling inputs
3. Connect cooling port flow properties to cooling inputs  
4. Mix cooling flow with primary flow via `ThermoAdd`
5. Adjust work extraction for cooling penalty
6. Expose `W_cool` and stage pressures as outputs

### BleedReinject Element

New file `pycycle/elements/bleed_reinject.py`:

```
BleedReinject
├── FlowIn - Fl_main
├── FlowIn - Fl_bleed_0 .. Fl_bleed_N
├── ThermoAdd(mix_mode='flow') - mix main + bleeds
├── Thermo(total_hP) - mixed total properties
├── Thermo(static_Ps | static_A) - mixed static properties
└── BalanceComp - area or pressure match
```

Conserves mass, enthalpy, and composition by construction via `ThermoAdd`.

### Mass Conservation Validation

Add to [`Cycle.configure()`](../../pycycle/mp_cycle.py:74):

```python
def _validate_mass_conservation(self):
    """Check that mass flow is conserved across the flow graph."""
    # For each node with multiple inputs/outputs, verify sum(W_in) == sum(W_out)
```

## Validation Approach

1. **Cooling consistency** — single cooling row on turbine; verify `W_cool` matches analytic correlation
2. **Work penalty** — turbine power with cooling < without cooling; verify correct reduction
3. **Bleed round-trip** — `BleedOut` → `BleedReinject`; verify mass and enthalpy conservation
4. **Full cycle** — turbofan with bleed and cooling; verify convergence and continuous properties at reinjection points
5. **Complete test assertions** — fill in the commented-out assertions in [`test_cooling.py`](../../pycycle/elements/test/test_cooling.py:140)

## Classification

| Mitigation | Type |
|-----------|------|
| Cooling-integrated turbine | INTEGRATE — adds option to existing element |
| `BleedReinject` element | INTEGRATE — new element using existing patterns |
| Mass conservation checks | MITIGATE — validation utility, no physics change |
| Standard naming conventions | MITIGATE — documentation only |
