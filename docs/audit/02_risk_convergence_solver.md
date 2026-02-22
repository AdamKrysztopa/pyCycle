# Risk 1: Convergence Robustness & Solver Stability

**Severity**: CRITICAL  
**Impact**: Solver divergence during off-design sweeps, nozzle choking transitions, and multi-point runs

## Current State in pyCycle

### Internal Newton Solvers

Several elements embed `NewtonSolver` with linesearch and bounds enforcement:

- **FlightConditions** — [`flight_conditions.py`](../../pycycle/elements/flight_conditions.py) uses Newton with `BoundsEnforceLS` to converge total temperature/pressure matching ambient static conditions
- **Mixer** — [`mixer.py`](../../pycycle/elements/mixer.py) contains `impulse_converge` group with Newton + `BoundsEnforceLS` for impulse balance
- **Nozzle** — [`nozzle.py`](../../pycycle/elements/nozzle.py) uses optional internal Newton when `internal_solver=True` for throat property convergence
- **Thermo** — [`thermo.py`](../../pycycle/thermo/thermo.py:163) always adds Newton with `ArmijoGoldsteinLS`, `maxiter=100`, `atol=1e-10`, `rtol=1e-10`

### Balance Components

- [`Nozzle`](../../pycycle/elements/nozzle.py:11) — `PR_bal` implicit component balances pressure ratio until calculated static pressure matches exhaust
- [`Mixer`](../../pycycle/elements/mixer.py) — balances total pressure to match impulse sum
- [`Thermo`](../../pycycle/thermo/thermo.py:82) — `BalanceComp` seeks temperature `T` matching target entropy or enthalpy

### Solver Tolerances

Hard-coded in each element with no unified control:

```python
# From thermo.py:163-170
newton.options['maxiter'] = 100
newton.options['atol'] = 1e-10
newton.options['rtol'] = 1e-10
newton.options['stall_limit'] = 4
newton.options['stall_tol'] = 1e-10
newton.options['solve_subsystems'] = True
```

## Identified Issues

### 1. No Continuation or Homotopy Strategy

Engine cycles exhibit discontinuities when:
- Nozzles choke or unchoke
- Afterburners ignite — when added
- Mixer pressures mismatch between streams
- Off-design operating points move far from design

There is no mechanism to gradually ramp parameters between operating points. Each `run_model()` call starts from whatever state the solver left.

### 2. Discrete Switch in Nozzle

The nozzle uses a hard `if/else` to select between static-pressure-based and Mach-number-based solutions at the choking boundary. This creates a **non-differentiable discontinuity** that Newton solvers cannot handle gracefully. Near the choke point, the solver oscillates between the two branches.

### 3. No Warm-Start API for Sweeps

[`MPCycle`](../../pycycle/mp_cycle.py:197) manages design/off-design points but provides no utility for sweeping across operating conditions — e.g., altitude/Mach/throttle envelopes — where the previous solution should seed the next case.

### 4. Element-Local Solver Settings

Each element configures its own Newton solver independently. Users cannot adjust solver parameters at the `Cycle` level — they must reach into individual elements to change tolerances, iteration limits, or linesearch settings.

### 5. Missing `guess_nonlinear` in Most Elements

Only [`ChemEq`](../../pycycle/thermo/cea/chem_eq.py:51) implements `guess_nonlinear()` to provide initial guesses. Other implicit components — `PsResid`, `PR_bal`, mixer balance — rely on default initial values which may be far from the solution.

### 6. No Solver Fallback

If Newton fails, there is no automatic fallback to a more robust — but slower — solver such as Broyden or `NonlinearBlockGS`. The user must manually reconfigure solvers.

## What Is Missing

| Gap | Description | Priority |
|-----|-------------|----------|
| `ContinuationManager` | Utility to ramp parameters gradually between operating points | HIGH |
| `solve_case_sequence()` | Warm-start method for deck sweeps on `MPCycle` | HIGH |
| Nozzle smooth blending | Replace discrete choke switch with logistic blending | HIGH |
| Unified solver configuration | Cycle-level solver options propagated to elements | MEDIUM |
| Solver fallback chain | Newton → Broyden → BlockGS fallback | MEDIUM |
| `guess_nonlinear` implementations | Initial guess methods for `PsResid`, `PR_bal`, mixer | MEDIUM |

## Proposed Mitigations

### Continuation Manager

New file `pycycle/solver_utils.py` with `ContinuationManager`:
- Takes a list of ramped parameters and target values
- Gradually varies them from benign starting values to targets
- If a step fails, reduces step size and retries
- Uses converged state as initial guess for next step

### Warm-Start Sweep

Extend `MPCycle` with `solve_case_sequence(cases)`:
- Accepts sequence of input dictionaries
- Sets new inputs without resetting unknowns
- Previous solution becomes initial guess for next case
- Leverages OpenMDAO's persistent state

### Nozzle Logistic Blending

Replace the discrete choke switch with a smooth logistic function:

```python
# Blending factor based on proximity to choked condition
deltaP = Ps_calc - Ps_choked
alpha = 0.5 * (1 + np.tanh(kappa * deltaP / Ps_calc))  # kappa ~ 50
# Smoothly blend between choked and unchoked solutions
```

This maintains differentiability across the choking boundary and allows Newton to converge.

### Solver Configuration Propagation

Add solver options to [`Element`](../../pycycle/element_base.py:9) and [`Cycle`](../../pycycle/mp_cycle.py:13):

```python
self.options.declare('solver_type', default='newton', values=['newton', 'broyden', 'nlbgs'])
self.options.declare('solver_atol', default=1e-10)
self.options.declare('solver_rtol', default=1e-10)
self.options.declare('solver_maxiter', default=100)
```

Cycle propagates these to child elements during `setup()`.

## Validation Approach

1. **Throttle sweep test** — sweep throttle from idle to max for a turbojet; verify monotonic thrust curve and no divergence at choke transition
2. **Regression tests** — existing examples must produce identical results within tolerance
3. **Derivative verification** — `check_partials()` on nozzle with smoothing enabled
4. **Conservation checks** — mass and energy conservation across all elements in a cycle

## Classification

| Mitigation | Type |
|-----------|------|
| `ContinuationManager` + warm-start | MITIGATE — sits on top of existing cycles |
| Nozzle smoothing | PATCH — modifies switch logic, preserves physics |
| Solver configuration propagation | INTEGRATE — modifies `Element`/`Cycle` architecture |
| Solver fallback chain | MITIGATE — wrapper around existing solvers |
