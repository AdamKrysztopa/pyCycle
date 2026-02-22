# Running pyCycle Examples

This guide explains how to set up and run the example cycles included in the pyCycle project.

## Prerequisites

- Python 3.10 or higher (3.12 recommended)
- UV package manager (for dependency management)
- OpenMDAO 3.10.0 or higher

## Project Setup

### 1. Environment Setup with UV

The project uses UV for fast and reliable dependency management. If you haven't already set up the environment:

```bash
# Create virtual environment
uv venv .venv --python 3.12

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows

# Install the project with all dependencies
uv pip install -e ".[all]"
```

### 2. Environment Variables

The project includes a `.env` file with configuration options:

```bash
# Virtual Environment Path
VIRTUAL_ENV=.venv

# Python Path - ensures project modules are importable
PYTHONPATH=${PYTHONPATH}:/path/to/pyCycle

# Optional: OpenMDAO Settings
# OPENMDAO_REPORTS_DIR=reports
# OPENMDAO_REQUIRE_MPI=0

# Optional: pyCycle Thermo Settings
# PYCYCLE_THERMO_DEFAULT=tabular  # Options: 'tabular' or 'cea'
```

## Available Examples

The `example_cycles` directory contains various thermodynamic cycle examples:

### Basic Examples

1. **Electric Propulsor** (`electric_propulsor.py`)
   - Simple electric propulsion system
   - Good starting point for beginners
   - Fast execution time

2. **Simple Turbojet** (`simple_turbojet.py`)
   - Basic turbojet engine cycle
   - Includes compressor, burner, turbine, and nozzle

3. **Single Spool Turboshaft** (`single_spool_turboshaft.py`)
   - Turboshaft configuration
   - Single spool design

4. **Wet Propulsor** (`wet_propulsor.py`)
   - Propulsion system with water injection

### Advanced Examples

5. **High Bypass Turbofan** (`high_bypass_turbofan.py`)
   - Commercial turbofan engine
   - Complex multi-spool configuration

6. **Mixedflow Turbofan** (`mixedflow_turbofan.py`)
   - Mixed exhaust flow configuration

7. **Afterburning Turbojet** (`afterburning_turbojet.py`)
   - Military-style engine with afterburner

8. **Multi-Spool Turboshaft** (`multi_spool_turboshaft.py`)
   - Advanced turboshaft with multiple spools

### NASA N+3 Reference Examples

The `example_cycles/N+3ref/` directory contains reference engines based on NASA's N+3 advanced engine studies:

- `N3ref.py` - Full N+3 reference engine
- `N3_MDP.py` - Mission Design Point
- `N3_SPD.py` - Sized Performance Design
- Component map files (Fan, LPC, HPC, LPT, HPT)

## Running Examples

### Method 1: Direct Execution (Recommended)

Navigate to the `example_cycles` directory and run the example:

```bash
cd example_cycles
python electric_propulsor.py
```

**Why this method?**
- Ensures proper module path resolution
- Simplest approach for individual examples
- Works with relative imports

### Method 2: From Project Root

Some examples can be run from the project root:

```bash
python -m example_cycles.electric_propulsor
```

### Method 3: Using testflo (For Testing)

Run all examples as tests:

```bash
# From project root - runs unit tests
testflo pycycle

# From example_cycles - runs benchmark tests
cd example_cycles
testflo -b .
```

## Example Output

When you run an example successfully, you'll see:

1. **Solver Iterations**: Newton solver convergence information
2. **Flow Stations**: Thermodynamic properties at various points
3. **Component Properties**: Performance characteristics of compressors, turbines, etc.
4. **Nozzle Properties**: Exit conditions and thrust calculations

Example output from `electric_propulsor.py`:

```
======
design
======
NL: Newton 0 ; 0.658111517 1
|  LS: BCHK 0 ; 44.2915348 67.3009569
NL: Newton 1 ; 0.0900132352 0.136775049
...
NL: Newton Converged

FLOW STATIONS
--------------------------------------------------------------------------------
Flow Station           |   tot:P    tot:T    tot:h    tot:S   stat:P  stat:W  ...
--------------------------------------------------------------------------------
design.fc.Fl_O         |   5.865  453.215  -21.871    1.662    3.834  409.636  ...
design.inlet.Fl_O      |   5.865  453.215  -21.871    1.662    4.616  409.636  ...
...
```

## Troubleshooting

### ModuleNotFoundError

**Problem**: `ModuleNotFoundError: No module named 'example_cycles'`

**Solution**: Run the script from the `example_cycles` directory:
```bash
cd example_cycles
python <script_name>.py
```

### Import Errors

**Problem**: Cannot import pycycle modules

**Solution**: 
1. Ensure you've installed the package: `uv pip install -e ".[all]"`
2. Activate the virtual environment: `source .venv/bin/activate`
3. Check PYTHONPATH includes the project root

### Numpy Compatibility Issues

**Problem**: `ValueError: setting an array element with a sequence`

**Solution**: This may occur with some examples using newer NumPy versions. Try:
1. Running a different example (e.g., `electric_propulsor.py` works reliably)
2. Checking if there are updates to pyCycle that address compatibility

### Solver Convergence Issues

**Problem**: Newton solver fails to converge

**Solution**:
1. Check initial conditions in the example script
2. Try adjusting solver tolerances
3. Review the example's specific requirements in comments

## Example-Specific Notes

### Electric Propulsor
- **Runtime**: ~0.4 seconds
- **Complexity**: Low
- **Best for**: Learning pyCycle basics

### Simple Turbojet
- **Runtime**: ~1-2 seconds
- **Complexity**: Medium
- **Requirements**: Basic understanding of jet engine cycles

### High Bypass Turbofan
- **Runtime**: ~5-10 seconds
- **Complexity**: High
- **Requirements**: Understanding of multi-spool turbomachinery

### N+3 Reference Examples
- **Runtime**: Variable, some are long-running
- **Complexity**: Very High
- **Requirements**: Familiarity with advanced engine concepts
- **Note**: These are research-grade examples

## Performance Considerations

### Using Tabular Thermodynamics

For faster execution, pyCycle supports tabular thermodynamic data:

```python
# In your cycle definition
prob = om.Problem()
prob.model = mp_cycle.Cycle(design=True, thermo_method='tabular', thermo_data=pyc.AIR_JETA_TAB_SPEC)
```

**Benefits**:
- 10-100x faster than CEA thermodynamics
- Good accuracy for standard conditions

**Limitations**:
- Fixed fuel type (Jet-A by default)
- Limited temperature range
- Requires pre-computed tables

### Generating Custom Thermo Tables

If you need different fuel types or conditions:

```bash
python example_cycles/tab_thermo_data_generator.py
```

## Next Steps

1. **Start Simple**: Begin with `electric_propulsor.py`
2. **Progress Gradually**: Move to `simple_turbojet.py`
3. **Explore Advanced**: Try turbofan and N+3 examples
4. **Modify Examples**: Experiment with parameters
5. **Create Custom Cycles**: Build your own using pyCycle components

## Additional Resources

- [pyCycle Paper](https://www.mdpi.com/2226-4310/6/8/87/pdf) - Detailed theoretical background
- [OpenMDAO Documentation](https://openmdao.org/) - Framework documentation
- Example source code - Best learning resource with inline comments
- `pycycle/docs/` - Additional technical documentation

## Testing Your Setup

Run this quick test to verify your installation:

```bash
# Activate environment
source .venv/bin/activate

# Navigate to examples
cd example_cycles

# Run the simplest example
python electric_propulsor.py

# If successful, you should see solver output and flow station tables
```

Success! If you see convergence messages and flow tables, your setup is working correctly.

## Common Commands Reference

```bash
# Setup
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all]"

# Run examples
cd example_cycles
python electric_propulsor.py

# Run tests
testflo pycycle                # Unit tests
cd example_cycles && testflo -b .  # Benchmark tests

# Generate documentation
cd pycycle/docs
make html
```

---

**Note**: This documentation assumes you have already set up the project following the installation instructions in the main README.md.
