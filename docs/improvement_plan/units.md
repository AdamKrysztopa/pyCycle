# Improvement Plan: Unit System

**Related audit**: [Risk 5: Unit Consistency](../audit/06_risk_unit_consistency.md)  
**Related PRs**: PR 8 — Unit System Support

---

## UNI-01: `unit_system` Option on Cycle and Element

**Current state**: No way to specify preferred unit system. Elements independently choose imperial or SI defaults.

**Improvement**: Add `unit_system` option to [`Cycle`](../../pycycle/mp_cycle.py:13) and [`Element`](../../pycycle/element_base.py:9):

```python
# In Cycle.initialize()
self.options.declare('unit_system', default='ENG', values=['ENG', 'SI'],
    desc='Unit system for default values and flow station outputs')

# In Element.initialize()
self.options.declare('unit_system', default='ENG', values=['ENG', 'SI'],
    desc='Unit system — inherited from parent Cycle')
```

Propagate in `Cycle.setup()` alongside other cycle-level options:

```python
cycle_level_options = ['thermo_method', 'thermo_data', 'design', 'unit_system']
```

**Files to modify**:
- [`pycycle/element_base.py`](../../pycycle/element_base.py:21) — add option
- [`pycycle/mp_cycle.py`](../../pycycle/mp_cycle.py:16) — add option and propagation

**Depends on**: Nothing  
**Risk**: LOW — adding option is non-breaking; behaviour change only when set to 'SI'

---

## UNI-02: Unit System Mappings

**Current state**: No centralised mapping between variable types and unit strings.

**Improvement**: New module `pycycle/unit_utils.py`:

```python
UNIT_SYSTEMS = {
    'ENG': {
        'temperature': 'degR',
        'pressure': 'lbf/inch**2',
        'mass_flow': 'lbm/s',
        'enthalpy': 'Btu/lbm',
        'entropy': 'Btu/(lbm*degR)',
        'velocity': 'ft/s',
        'area': 'inch**2',
        'density': 'lbm/ft**3',
        'power': 'hp',
        'torque': 'ft*lbf',
        'force': 'lbf',
        'length': 'ft',
        'gas_constant': 'Btu/(lbm*degR)',
        'specific_heat': 'Btu/(lbm*degR)',
    },
    'SI': {
        'temperature': 'degK',
        'pressure': 'Pa',
        'mass_flow': 'kg/s',
        'enthalpy': 'J/kg',
        'entropy': 'J/(kg*degK)',
        'velocity': 'm/s',
        'area': 'm**2',
        'density': 'kg/m**3',
        'power': 'W',
        'torque': 'N*m',
        'force': 'N',
        'length': 'm',
        'gas_constant': 'J/(kg*degK)',
        'specific_heat': 'J/(kg*degK)',
    }
}

def get_unit(var_type: str, system: str = 'ENG') -> str:
    """Get the unit string for a variable type in the given system."""
    return UNIT_SYSTEMS[system][var_type]

def get_default_value(var_type: str, system: str = 'ENG') -> float:
    """Get a sensible default value for a variable type."""
    defaults_eng = {
        'temperature': 518.67,    # degR - standard day
        'pressure': 14.696,       # psi - sea level
        'mass_flow': 100.0,       # lbm/s
        'enthalpy': -20.0,        # Btu/lbm
        'entropy': 1.66,          # Btu/(lbm*degR)
        'velocity': 500.0,        # ft/s
        'area': 500.0,            # inch**2
    }
    defaults_si = {
        'temperature': 288.15,    # degK - standard day
        'pressure': 101325.0,     # Pa - sea level
        'mass_flow': 45.0,        # kg/s
        'enthalpy': -46500.0,     # J/kg
        'entropy': 6950.0,        # J/(kg*degK)
        'velocity': 150.0,        # m/s
        'area': 0.32,             # m**2
    }
    return (defaults_eng if system == 'ENG' else defaults_si).get(var_type)
```

**Files to create**: `pycycle/unit_utils.py`  
**Depends on**: UNI-01  
**Risk**: LOW — new utility module

---

## UNI-03: Generic UnitProps Component

**Current state**: [`EngUnitProps`](../../pycycle/thermo/unit_comps.py:51) hard-codes imperial units for flow station outputs. Its name encodes "Eng" = English.

**Improvement**: Replace with `FlowUnitProps` that respects `unit_system`:

```python
class FlowUnitProps(UnitCompBase):
    """Convert internal thermo properties to user's preferred unit system."""
    
    def initialize(self):
        super().initialize()
        self.options.declare('unit_system', default='ENG', values=['ENG', 'SI'])
    
    def setup_io(self, composition):
        system = self.options['unit_system']
        
        self.add_input('T', val=284., units=get_unit('temperature', system))
        self.add_input('P', val=1., units=get_unit('pressure', system))
        self.add_input('h', val=1., units=get_unit('enthalpy', system))
        self.add_input('S', val=1., units=get_unit('entropy', system))
        self.add_input('gamma', val=1.4)
        self.add_input('Cp', val=1., units=get_unit('specific_heat', system))
        self.add_input('Cv', val=1., units=get_unit('specific_heat', system))
        self.add_input('rho', val=1., units=get_unit('density', system))
        self.add_input('R', val=1., units=get_unit('gas_constant', system))
        # ...composition...
        
        super().setup_io()
```

Keep `EngUnitProps` as a deprecated alias.

**Files to modify**: [`pycycle/thermo/unit_comps.py`](../../pycycle/thermo/unit_comps.py)  
**Depends on**: UNI-01, UNI-02  
**Risk**: MEDIUM — changes flow station output units when SI is selected

---

## UNI-04: Deprecate `g_c` Usage

**Current state**: [`g_c = 32.174`](../../pycycle/constants.py:61) is used in nozzle thrust and other force calculations. In SI, `g_c = 1` by definition.

**Improvement**: Replace explicit `g_c` usage with proper OpenMDAO unit handling:

### Example — Nozzle Thrust

```python
# Current
self.add_output('Fg', units='lbf')
Fg = W * V / g_c + (Ps - P_ambient) * A / g_c

# Improved — let OpenMDAO handle the conversion
self.add_output('Fg', units='lbf')  # or 'N' for SI
# W is in lbm/s, V in ft/s → W*V is in lbm*ft/s²
# OpenMDAO knows that 1 lbf = 32.174 lbm*ft/s²
Fg = W * V  # natural units, let unit framework convert
```

**Phase 1**: Keep `g_c` but add deprecation warning when accessed  
**Phase 2**: Remove `g_c` usage from all elements

**Files to modify**:
- [`pycycle/constants.py`](../../pycycle/constants.py:61) — deprecation
- [`pycycle/elements/nozzle.py`](../../pycycle/elements/nozzle.py) — thrust calculation
- [`pycycle/elements/performance.py`](../../pycycle/elements/performance.py) — if applicable
- Any other files using `g_c`

**Depends on**: UNI-01  
**Risk**: MEDIUM — correctness-critical; requires careful validation

---

## UNI-05: Standard-Day Reference Values

**Current state**: Corrected flow uses imperial standard-day values:
```python
T_STDeng = 518.67   # degR
P_STDeng = 14.695951 # psi
```

These are used in [`compressor.py`](../../pycycle/elements/compressor.py:39) for theta/delta calculations.

**Improvement**: Add SI equivalents and select based on `unit_system`:

```python
STD_DAY = {
    'ENG': {'T': 518.67, 'T_units': 'degR', 'P': 14.695951, 'P_units': 'lbf/inch**2'},
    'SI':  {'T': 288.15, 'T_units': 'degK', 'P': 101325.0, 'P_units': 'Pa'}
}
```

Since corrected flow corrections are based on ratios — theta = T/T_std, delta = P/P_std — the results are dimensionless and unit-system-independent. But having the proper reference values improves clarity.

**Files to modify**: [`pycycle/constants.py`](../../pycycle/constants.py)  
**Depends on**: UNI-02  
**Risk**: LOW

---

## UNI-06: FlowIn Unit Awareness

**Current state**: [`FlowIn`](../../pycycle/flow_in.py) hard-codes imperial units for all inputs — degR, psi, lbm/s.

**Improvement**: Accept `unit_system` option and set units accordingly:

```python
class FlowIn(om.ExplicitComponent):
    def initialize(self):
        self.options.declare('fl_name', default='flow')
        self.options.declare('unit_system', default='ENG', values=['ENG', 'SI'])
    
    def setup(self):
        system = self.options['unit_system']
        T_unit = get_unit('temperature', system)
        P_unit = get_unit('pressure', system)
        # etc.
        
        self.add_input(f'{fl_name}:tot:T', val=518., units=T_unit, ...)
```

**Files to modify**: [`pycycle/flow_in.py`](../../pycycle/flow_in.py)  
**Depends on**: UNI-01, UNI-02  
**Risk**: MEDIUM

---

## Summary

| ID | Improvement | Priority | Risk | Phase |
|----|------------|----------|------|-------|
| UNI-01 | `unit_system` option | MEDIUM | LOW | 2 |
| UNI-02 | Unit mappings module | MEDIUM | LOW | 2 |
| UNI-03 | Generic UnitProps | MEDIUM | MEDIUM | 2 |
| UNI-04 | Deprecate `g_c` | LOW | MEDIUM | 3 |
| UNI-05 | SI standard-day refs | LOW | LOW | 2 |
| UNI-06 | FlowIn unit awareness | MEDIUM | MEDIUM | 2 |
