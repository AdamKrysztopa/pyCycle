# Improvement Plan: Solver & Convergence

**Related audit**: [Risk 1: Convergence & Solver Stability](../audit/02_risk_convergence_solver.md)  
**Related PRs**: PR 1 — Nozzle Smoothing, PR 2 — Solver Utils

---

## SOL-01: Continuation Manager

**Current state**: No utility exists to gradually ramp parameters between operating points. Users must manually adjust inputs and call `run_model()` repeatedly.

**Improvement**: New class `ContinuationManager` in `pycycle/solver_utils.py`:

```python
class ContinuationManager:
    """Ramp parameters from starting values to targets with adaptive stepping."""
    
    def __init__(self, problem: om.Problem):
        self.prob = problem
        self.n_steps = 5
        self.min_step_fraction = 0.01
        self.max_retries = 3
    
    def ramp(self, param_schedule: dict[str, tuple[float, float]], 
             units: dict[str, str] = None) -> list[dict]:
        """
        Ramp parameters from start to end values.
        
        param_schedule: {var_name: (start_value, end_value)}
        Returns: list of result dicts for each converged step
        """
```

**Key features**:
- Adaptive step size — halve step on failure, double on easy convergence
- State preservation — previous converged solution seeds next step
- Callback support — user function called after each converged step
- Failure handling — configurable max retries before giving up
- Result collection — returns list of results for each step

**Use cases**:
- Ramping afterburner FAR from 0 to target
- Sweeping nozzle area ratio during variable-geometry changes
- Transitioning between design and far-off-design conditions

**Files to create**: `pycycle/solver_utils.py`  
**Depends on**: Nothing  
**Risk**: LOW — utility class, no existing code changes

---

## SOL-02: Warm-Start Sweep on MPCycle

**Current state**: [`MPCycle`](../../pycycle/mp_cycle.py:197) manages design/off-design points but provides no utility for operating envelope sweeps.

**Improvement**: Add `solve_case_sequence()` method to `MPCycle`:

```python
def solve_case_sequence(self, cases: list[dict], 
                         point_name: str = None) -> list[dict]:
    """
    Run a sequence of operating points with warm-starting.
    
    Each case is a dict of {variable_name: (value, units)}.
    The previous converged solution seeds the next case.
    
    Parameters
    ----------
    cases : list of dict
        Sequence of operating conditions to evaluate
    point_name : str, optional
        Which operating point to sweep. If None, uses the first off-design point.
    
    Returns
    -------
    list of dict
        Results for each converged case
    """
```

**Key features**:
- No state reset between cases — OpenMDAO preserves unknowns
- Sort cases by proximity — optional auto-ordering for efficiency
- Skip failed cases — continue with next instead of aborting
- Collect outputs — user specifies which variables to extract

**Files to modify**: [`pycycle/mp_cycle.py`](../../pycycle/mp_cycle.py)  
**Depends on**: Nothing  
**Risk**: LOW

---

## SOL-03: Unified Solver Configuration

**Current state**: Each element configures its own Newton solver independently in `setup()`. Tolerances are hardcoded — e.g., [`thermo.py`](../../pycycle/thermo/thermo.py:163) sets `atol=1e-10`, `maxiter=100`.

**Improvement**: Add solver configuration options to [`Element`](../../pycycle/element_base.py:9) and [`Cycle`](../../pycycle/mp_cycle.py:13):

```python
# In Element.initialize()
self.options.declare('solver_type', default=None,
    desc='Override solver type: newton, broyden, nlbgs. None = use element default.')
self.options.declare('solver_atol', default=None,
    desc='Override absolute tolerance. None = use element default.')
self.options.declare('solver_rtol', default=None,
    desc='Override relative tolerance. None = use element default.')
self.options.declare('solver_maxiter', default=None,
    desc='Override max iterations. None = use element default.')
self.options.declare('solver_linesearch', default=None,
    desc='Override linesearch: armijo, bounds, none. None = use element default.')
```

In `Cycle.setup()`, propagate these to child elements:

```python
solver_opts = ['solver_type', 'solver_atol', 'solver_rtol', 'solver_maxiter', 'solver_linesearch']
for child_name, child in self._children.items():
    for opt in solver_opts:
        if opt in child.options and self.options.get(opt) is not None:
            child.options[opt] = self.options[opt]
```

**Files to modify**:
- [`pycycle/element_base.py`](../../pycycle/element_base.py)
- [`pycycle/mp_cycle.py`](../../pycycle/mp_cycle.py)
- [`pycycle/thermo/thermo.py`](../../pycycle/thermo/thermo.py) — use options instead of hardcoded values

**Depends on**: Nothing  
**Risk**: LOW

---

## SOL-04: Solver Fallback Chain

**Current state**: If Newton fails, the user must manually reconfigure solvers.

**Improvement**: Add a utility that wraps solver execution with fallback:

```python
class SolverFallbackChain:
    """Try solvers in sequence until one converges."""
    
    def __init__(self, group: om.Group):
        self.group = group
        self.chain = [
            ('newton', {'maxiter': 50, 'atol': 1e-10}),
            ('newton', {'maxiter': 100, 'atol': 1e-8}),  # relaxed
            ('broyden', {'maxiter': 200, 'atol': 1e-8}),
        ]
    
    def solve(self):
        """Try each solver in the chain until convergence."""
```

**Files to create**: Add to `pycycle/solver_utils.py`  
**Depends on**: SOL-01 — same file  
**Risk**: LOW

---

## SOL-05: `guess_nonlinear` Implementations

**Current state**: Only [`ChemEq`](../../pycycle/thermo/cea/chem_eq.py:51) implements `guess_nonlinear()`. Other implicit components rely on default initial values.

**Improvement**: Add `guess_nonlinear()` to:

1. **[`PsResid`](../../pycycle/thermo/static_ps_resid.py:8)** — estimate Ps from isentropic relations:
   ```python
   def guess_nonlinear(self, inputs, outputs, resids):
       gamma = inputs['guess:gamt']
       Pt = inputs['guess:Pt']
       if self.options['mode'] == 'MN':
           MN = inputs['MN']
           outputs['Ps'] = Pt * (1 + (gamma-1)/2 * MN**2)**(-gamma/(gamma-1))
       elif self.options['mode'] == 'area':
           outputs['MN'] = inputs['guess:MN']
           outputs['Ps'] = Pt * 0.5  # rough initial guess
   ```

2. **[`PR_bal`](../../pycycle/elements/nozzle.py:11)** — estimate PR from upstream conditions:
   ```python
   def guess_nonlinear(self, inputs, outputs, resids):
       outputs['PR'] = max(1.001, inputs['Ps_exhaust'] / inputs['Ps_calc'] * 2.0)
   ```

3. **Mixer balance** — estimate total pressure from stream momenta

**Files to modify**:
- [`pycycle/thermo/static_ps_resid.py`](../../pycycle/thermo/static_ps_resid.py)
- [`pycycle/elements/nozzle.py`](../../pycycle/elements/nozzle.py)
- [`pycycle/elements/mixer.py`](../../pycycle/elements/mixer.py)

**Depends on**: Nothing  
**Risk**: LOW — only affects initial guess, not converged solution

---

## SOL-06: Thermo Solver Isolation

**Current state**: The TODO in [`thermo.py`](../../pycycle/thermo/thermo.py:122) notes:
> "Move the newton stuff into a convergence sub-group that doesn't include this"

The Newton solver in `Thermo` encompasses both the property calculations and the unit conversion passthroughs. The passthroughs don't need Newton iteration.

**Improvement**: Create an internal `converge` group:

```python
class Thermo(om.Group):
    def setup(self):
        # Convergence sub-group with Newton
        converge = self.add_subsystem('converge', om.Group())
        converge.add_subsystem('base_thermo', base_thermo, ...)
        if mode != 'total_TP':
            converge.add_subsystem('balance', ...)
        
        # Newton only on convergence group
        newton = converge.nonlinear_solver = om.NewtonSolver()
        converge.linear_solver = om.DirectSolver()
        
        # Unit conversions outside Newton
        self.add_subsystem('flow', EngUnitProps(...), ...)
```

**Files to modify**: [`pycycle/thermo/thermo.py`](../../pycycle/thermo/thermo.py)  
**Depends on**: Nothing  
**Risk**: MEDIUM — restructures internal groups

---

## SOL-07: Tabular Thermo T/P Range Bounds

**Current state**: The TODO in [`thermo.py`](../../pycycle/thermo/thermo.py:84) notes:
> "need to add some kind of T/P ranges to the tabular thermo somehow"

Currently hard-coded:
```python
upper = 2500.  # degK for tabular
lower = 150.   # degK for tabular
```

**Improvement**: Extract T/P bounds from the tabular data itself:

```python
if method == "TABULAR":
    spec = thermo_kwargs.get('spec', AIR_JETA_TAB_SPEC)
    lower = float(spec['T'].min())
    upper = float(spec['T'].max())
```

This ensures the solver balance bounds match the table coverage.

**Files to modify**: [`pycycle/thermo/thermo.py`](../../pycycle/thermo/thermo.py)  
**Depends on**: Nothing  
**Risk**: LOW

---

## Summary

| ID | Improvement | Priority | Risk | Phase |
|----|------------|----------|------|-------|
| SOL-01 | Continuation Manager | HIGH | LOW | 1 |
| SOL-02 | Warm-start sweep | HIGH | LOW | 1 |
| SOL-03 | Unified solver config | MEDIUM | LOW | 1 |
| SOL-04 | Solver fallback chain | MEDIUM | LOW | 1 |
| SOL-05 | `guess_nonlinear` implementations | MEDIUM | LOW | 1 |
| SOL-06 | Thermo solver isolation | LOW | MEDIUM | 2 |
| SOL-07 | Tabular T/P range bounds | MEDIUM | LOW | 1 |
