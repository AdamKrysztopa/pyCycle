# pyCycle Quick Reference Guide

## Installation & Setup

```bash
# Create virtual environment with UV
uv venv .venv --python 3.12

# Activate environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install with all dependencies
uv pip install -e ".[all]"
```

## Running Examples

```bash
# Navigate to examples
cd example_cycles

# Run an example
python electric_propulsor.py

# Run an example with SI outputs
python electric_propulsor.py --unit-system SI

# Run all tests
testflo pycycle

# Run benchmark tests
testflo -b .
```

## Available Examples (by Complexity)

### ⭐ Beginner
| File | Description | Runtime |
|------|-------------|---------|
| `electric_propulsor.py` | Simple electric propulsion | ~0.4s |
| `wet_propulsor.py` | Propulsor with water injection | ~0.5s |

### ⭐⭐ Intermediate
| File | Description | Runtime |
|------|-------------|---------|
| `simple_turbojet.py` | Basic turbojet cycle | ~1-2s |
| `single_spool_turboshaft.py` | Single spool turboshaft | ~1-2s |
| `wet_simple_turbojet.py` | Turbojet with water injection | ~1-2s |

### ⭐⭐⭐ Advanced
| File | Description | Runtime |
|------|-------------|---------|
| `high_bypass_turbofan.py` | Commercial turbofan | ~5-10s |
| `mixedflow_turbofan.py` | Mixed exhaust turbofan | ~5-10s |
| `afterburning_turbojet.py` | Military turbojet | ~3-5s |
| `multi_spool_turboshaft.py` | Multi-spool turboshaft | ~3-5s |

### ⭐⭐⭐⭐ Expert (N+3ref/)
| File | Description | Note |
|------|-------------|------|
| `N3ref.py` | NASA N+3 reference engine | Research grade |
| `N3_MDP.py` | Mission Design Point | Multi-point optimization |
| `N3_SPD.py` | Sized Performance Design | Complex constraints |

## Basic pyCycle API

### Create a Cycle
```python
import openmdao.api as om
import pycycle.api as pyc

prob = om.Problem()
prob.model = pyc.Cycle(design=True)
# Optional explicit unit system selection
# prob.model = pyc.Cycle(design=True, unit_system='SI')
```

### Add Components
```python
# Flight conditions
prob.model.add_subsystem('fc', pyc.FlightConditions())

# Inlet
prob.model.add_subsystem('inlet', pyc.Inlet())

# Compressor/Fan
prob.model.add_subsystem('comp', pyc.Compressor())

# Combustor
prob.model.add_subsystem('burner', pyc.Combustor())

# Turbine
prob.model.add_subsystem('turb', pyc.Turbine())

# Nozzle
prob.model.add_subsystem('nozz', pyc.Nozzle())
```

### Connect Flow Stations
```python
# Connect flow between components
prob.model.pyc_connect_flow('fc.Fl_O', 'inlet.Fl_I')
prob.model.pyc_connect_flow('inlet.Fl_O', 'comp.Fl_I')
prob.model.pyc_connect_flow('comp.Fl_O', 'burner.Fl_I')
prob.model.pyc_connect_flow('burner.Fl_O', 'turb.Fl_I')
prob.model.pyc_connect_flow('turb.Fl_O', 'nozz.Fl_I')
```

### Setup and Run
```python
# Setup the problem
prob.setup()

# Set initial conditions
prob.set_val('fc.alt', 0.0, units='ft')
prob.set_val('fc.MN', 0.8)
# ... more initial values

# Run the model
prob.run_model()

# View results
prob.model.list_outputs()
```

## Common Component Parameters

### FlightConditions
```python
'fc.alt'      # Altitude (ft)
'fc.MN'       # Mach number
'fc.dTs'      # Temperature deviation from standard (degR)
```

### Compressor/Fan
```python
'comp.PR'     # Pressure ratio
'comp.eff'    # Adiabatic efficiency
'comp.map.RlineMap'  # Map R-line parameter
# Optional bleed controls (dimensionless fractions)
'comp.<bleed>:frac_W'     # W_bleed / W_in (local compressor inlet basis)
'comp.<bleed>:frac_P'     # (Pt_bleed - Pt_in) / (Pt_out - Pt_in)
'comp.<bleed>:frac_work'  # (ht_bleed - ht_in) / (ht_out - ht_in)
```

### Combustor
```python
'burner.MN'        # Exit Mach number
'burner.dPqP'      # Pressure loss fraction
'burner.Fl_I:FAR'  # Fuel-to-air ratio
```

### Turbine
```python
'turb.PR'     # Pressure ratio
'turb.eff'    # Adiabatic efficiency
# Turbine bleed pressure placement fraction (dimensionless)
'turb.<bleed>:frac_P'  # Pt_bleed = Pt_out + frac_P * (Pt_in - Pt_out)
```

### BleedOut
```python
'bld.<bleed>:frac_W'  # W_bleed / W_in at that BleedOut element inlet
```

### Nozzle
```python
'nozz.Cv'     # Velocity coefficient
'nozz.switchRegulator'  # Nozzle type
```

## Thermodynamic Options

### CEA (Chemical Equilibrium)
```python
prob.model = pyc.Cycle(
    design=True, 
    thermo_method='cea',
    thermo_data=pyc.species_data.janaf
)
```
- Full thermochemical calculations
- Any fuel composition
- Slower execution

### Tabular
```python
prob.model = pyc.Cycle(
    design=True,
    thermo_method='tabular',
    thermo_data=pyc.AIR_JETA_TAB_SPEC
)
```
- Pre-computed tables
- 10-100x faster
- Fixed fuel type (Jet-A default)

## Output Interpretation

### Flow Station Properties
| Property | Description | Units |
|----------|-------------|-------|
| `tot:P` | Total pressure | psia |
| `tot:T` | Total temperature | degR |
| `tot:h` | Total enthalpy | Btu/lbm |
| `tot:S` | Total entropy | Btu/(lbm·degR) |
| `stat:W` | Mass flow rate | lbm/s |
| `stat:MN` | Mach number | - |
| `stat:V` | Velocity | ft/s |

### Compressor Properties
| Property | Description |
|----------|-------------|
| `Wc` | Corrected mass flow |
| `Pr` | Pressure ratio |
| `eta_a` | Adiabatic efficiency |
| `eta_p` | Polytropic efficiency |
| `Nc` | Corrected speed |
| `pwr` | Power (negative = consumed) |

### Turbine Properties
| Property | Description |
|----------|-------------|
| `Wc` | Corrected mass flow |
| `Pr` | Pressure ratio |
| `eta_a` | Adiabatic efficiency |
| `eta_p` | Polytropic efficiency |
| `pwr` | Power (positive = produced) |

### Nozzle Properties
| Property | Description |
|----------|-------------|
| `PR` | Pressure ratio |
| `Cv` | Velocity coefficient |
| `Fg` | Gross thrust |
| `V` | Exit velocity |

## Solver Settings

### Newton Solver
```python
newton = prob.model.nonlinear_solver = om.NewtonSolver()
newton.options['maxiter'] = 50
newton.options['atol'] = 1e-8
newton.options['rtol'] = 1e-8
newton.options['iprint'] = 2
newton.options['solve_subsystems'] = True
```

### Linear Solver
```python
prob.model.linear_solver = om.DirectSolver()
```

## Common Issues & Solutions

### Issue: ModuleNotFoundError
```bash
# Solution: Run from example_cycles directory
cd example_cycles
python <script>.py
```

### Issue: Solver doesn't converge
```python
# Solution: Adjust initial conditions or tolerances
newton.options['maxiter'] = 100
newton.options['rtol'] = 1e-6
```

### Issue: Import errors
```bash
# Solution: Reinstall package
uv pip install -e ".[all]"
```

## Useful Commands

```bash
# List installed packages
uv pip list

# Freeze dependencies
uv pip freeze > requirements.txt

# Run specific test
testflo pycycle/elements/test/test_compressor.py

# Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

## Performance Tips

1. **Use tabular thermo** for production runs
2. **Start with tight convergence** tolerances for design point
3. **Relax tolerances** for off-design sweeps
4. **Use component maps** for realistic performance
5. **Cache expensive calculations** when possible

## File Locations

```
Project Root/
├── .env                  # Environment configuration
├── pyproject.toml        # Project dependencies
├── docs/                 # Documentation (you are here)
├── example_cycles/       # Examples
├── pycycle/             # Library source
│   ├── elements/        # Components
│   ├── thermo/          # Thermodynamics
│   └── maps/            # Performance maps
└── .venv/               # Virtual environment
```

## Units

pyCycle uses English Engineering units by default:
- Length: feet (ft)
- Mass: pounds-mass (lbm)
- Time: seconds (s)
- Temperature: Rankine (degR)
- Pressure: psia
- Force: pounds-force (lbf)

Convert using OpenMDAO's unit conversion:
```python
prob.set_val('fc.alt', 10000, units='m')  # Converts from meters
```

## Additional Resources

- **Detailed Guide**: [RUNNING_EXAMPLES.md](RUNNING_EXAMPLES.md)
- **Project Info**: [README.md](README.md)
- **Main README**: `../README.md`
- **Research Paper**: [MDPI Aerospace](https://www.mdpi.com/2226-4310/6/8/87/pdf)
- **OpenMDAO**: [openmdao.org](https://openmdao.org/)

---

**Pro Tip**: Start with `electric_propulsor.py`, then progress to `simple_turbojet.py`, then try modifying parameters to understand the effects.
