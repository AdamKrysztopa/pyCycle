# pyCycle Documentation

Welcome to the pyCycle documentation! This directory contains guides and documentation for using pyCycle effectively.

## Documentation Files

### Getting Started
- **[RUNNING_EXAMPLES.md](RUNNING_EXAMPLES.md)** - Complete guide on how to run the example cycles

### Quick Start

#### 1. Installation
```bash
# Create and activate virtual environment with UV
uv venv .venv --python 3.12
source .venv/bin/activate

# Install pyCycle with all dependencies
uv pip install -e ".[all]"
```

#### 2. Run Your First Example
```bash
cd example_cycles
python electric_propulsor.py
```

#### 3. Expected Output
You should see Newton solver convergence and flow station tables displaying thermodynamic properties.

## Project Structure

```
pyCycle/
├── pycycle/              # Main library code
│   ├── elements/         # Component models (compressor, turbine, etc.)
│   ├── thermo/           # Thermodynamic packages (CEA, tabular)
│   └── maps/             # Component performance maps
├── example_cycles/       # Example engine cycles
│   ├── electric_propulsor.py
│   ├── simple_turbojet.py
│   ├── high_bypass_turbofan.py
│   └── N+3ref/           # NASA N+3 reference engines
├── docs/                 # This documentation directory
└── pyproject.toml        # Project configuration and dependencies
```

## Key Concepts

### Thermodynamic Cycles
pyCycle models gas turbine engines as interconnected thermodynamic components:
- **FlightConditions**: Ambient conditions
- **Inlet**: Air intake
- **Compressor/Fan**: Compression stages
- **Combustor**: Fuel burning
- **Turbine**: Power extraction
- **Nozzle**: Thrust generation

### Thermodynamic Packages

#### CEA (Chemical Equilibrium with Applications)
- Full thermochemical calculations
- Accurate but slower
- Supports any fuel composition

#### Tabular
- Pre-computed thermodynamic tables
- 10-100x faster than CEA
- Fixed fuel type (default: Jet-A)

### Design vs Off-Design
- **Design Point**: Initial engine sizing and component selection
- **Off-Design**: Performance at various operating conditions

## Example Difficulty Levels

### Beginner
- `electric_propulsor.py` - Simple propulsion system
- Good for learning pyCycle API

### Intermediate
- `simple_turbojet.py` - Basic jet engine
- `single_spool_turboshaft.py` - Turboshaft engine
- `wet_propulsor.py` - Water injection system

### Advanced
- `high_bypass_turbofan.py` - Commercial turbofan
- `mixedflow_turbofan.py` - Mixed exhaust configuration
- `afterburning_turbojet.py` - Military engine

### Expert
- `N+3ref/` examples - NASA advanced engine concepts
- Multi-point optimization
- Custom component development

## Common Tasks

### Viewing Results
Results are printed to console as formatted tables showing:
- Flow properties (pressure, temperature, enthalpy)
- Component performance (efficiency, pressure ratio, power)
- Overall performance (thrust, fuel flow, TSFC)

### Modifying Examples
1. Copy an example as a starting point
2. Modify component parameters
3. Adjust design points or constraints
4. Run and analyze results

### Creating Custom Cycles
```python
import openmdao.api as om
import pycycle.api as pyc

# Create a cycle
prob = om.Problem()
prob.model = pyc.Cycle(design=True)

# Add components
prob.model.add_subsystem('fc', pyc.FlightConditions())
prob.model.add_subsystem('inlet', pyc.Inlet())
# ... add more components

# Connect flows
prob.model.pyc_connect_flow('fc.Fl_O', 'inlet.Fl_I')
# ... more connections

# Setup and run
prob.setup()
prob.run_model()
```

## Performance Tips

1. **Use Tabular Thermo**: 10-100x faster for standard cases
2. **Start with DESIGN**: Get initial sizing before off-design
3. **Check Convergence**: Monitor Newton solver output
4. **Adjust Tolerances**: Balance accuracy vs speed
5. **Use Component Maps**: More realistic than simple models

## Testing

### Run Unit Tests
```bash
testflo pycycle
```

### Run Example Benchmarks
```bash
cd example_cycles
testflo -b .
```

## Additional Resources

- **Main README**: `../README.md` - Installation and project overview
- **API Documentation**: `../pycycle/docs/` - Detailed API reference
- **Research Paper**: [pyCycle: A Tool for Efficient Optimization of Gas Turbine Engine Cycles](https://www.mdpi.com/2226-4310/6/8/87/pdf)
- **OpenMDAO Docs**: [openmdao.org](https://openmdao.org/) - Framework documentation

## Getting Help

1. Check example source code - heavily commented
2. Review error messages - often indicate the issue
3. Verify environment setup - ensure all dependencies installed
4. Check OpenMDAO compatibility - see version table in README

## Environment Configuration

The `.env` file in the project root contains:
```bash
VIRTUAL_ENV=.venv
PYTHONPATH=${PYTHONPATH}:/path/to/pyCycle
```

Additional optional settings:
- `OPENMDAO_REPORTS_DIR` - Output directory for OpenMDAO reports
- `PYCYCLE_THERMO_DEFAULT` - Default thermodynamic package

## Development Workflow

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Make changes to code

# 3. Run tests
testflo pycycle

# 4. Run example to verify
cd example_cycles
python electric_propulsor.py

# 5. Generate documentation (if needed)
cd ../pycycle/docs
make html
```

## Code Quality Fix Log (2026-02)

This section documents the code-quality cleanup and follow-up fixes, including how the work was split and why example execution broke temporarily.

### What was wrong

- The public API module [`pycycle/api.py`](../pycycle/api.py:1) was empty, so `import pycycle.api as pyc` did not expose core symbols like `Cycle`, maps, elements, and helpers. This caused example scripts (e.g. [`example_cycles/simple_turbojet.py`](../example_cycles/simple_turbojet.py:1)) to fail with `AttributeError: module 'pycycle.api' has no attribute 'Cycle'`.
- The CEA species data module did not re-export thermo datasets, so imports like `from pycycle.thermo.cea.species_data import janaf` failed during example startup. This broke CEA-based elements via [`pycycle/thermo/cea/thermo_add.py`](../pycycle/thermo/cea/thermo_add.py:1).
- Ruff reported a large set of unused imports/variables and bare `except` blocks across examples, tests, and core modules. Ruff auto-fix handled most of these, then remaining errors were fixed manually.
- Pyright was run for visibility, but it reported many issues due to OpenMDAO dynamic patterns and example/test code. Per instruction, no Pyright configuration changes or error suppressions were applied.

### How the work was split (conceptual commits)

1. **Tooling sync**: Added `ruff` and `pyright` to the dev extras in [`pyproject.toml`](../pyproject.toml:41) and synced with `uv sync --extra dev`.
2. **Ruff auto-fix**: Ran `ruff check . --fix` and `ruff format .` to address most F401/F841 and formatting issues.
3. **Ruff manual fixes**: Removed remaining unused variables/imports and addressed unsafe patterns, e.g. in [`pycycle/thermo/cea/chem_eq.py`](../pycycle/thermo/cea/chem_eq.py:141) and test files under [`pycycle/elements/test`](../pycycle/elements/test/test_cfd_start.py:1).
4. **API restoration**: Rebuilt [`pycycle/api.py`](../pycycle/api.py:1) to export elements, maps, cycle classes, constants, and viewers used by examples.
5. **CEA dataset exports**: Re-exported `janaf`, `wet_air`, and `co2_co_o2` from [`pycycle/thermo/cea/species_data.py`](../pycycle/thermo/cea/species_data.py:1) to restore legacy import paths used by examples/tests.

### Ruff/Pyright status

- **Ruff**: Clean after fixes (`ruff check .` passes).
- **Pyright**: Reported ~1200 errors across examples/tests and OpenMDAO-heavy modules; no config changes were made per instruction (see terminal output from the `uv run pyright` invocation).

### Example verification

- Verified: `uv run python example_cycles/simple_turbojet.py` now runs successfully after the API and species data exports were restored (see terminal output in this session).

## Version Compatibility

| pyCycle | OpenMDAO | Python |
|---------|----------|--------|
| 4.4.x   | ≥3.10.0  | ≥3.10  |
| 4.2.0   | ≥3.10.0  | ≥3.7   |
| 4.1.x   | ≥3.10.0  | ≥3.6   |

Current installation uses:
- Python 3.12.12
- OpenMDAO 3.42.0
- NumPy 2.4.2

## Contributing

When adding new examples or documentation:
1. Follow existing code style
2. Add descriptive comments
3. Create benchmark tests if applicable
4. Update documentation

---

**Last Updated**: February 2026
**pyCycle Version**: 4.4.1.dev0
