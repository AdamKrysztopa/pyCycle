"""Run selected examples in ENG and SI and generate a report."""

from __future__ import annotations

from pathlib import Path

import openmdao.api as om

from electric_propulsor import MPpropulsor
from multi_spool_turboshaft import MPMultiSpool
from simple_turbojet import MPTurbojet


def _s(prob, path: str, units: str | None = None) -> float:
    if units is None:
        return float(prob.get_val(path)[0])
    return float(prob.get_val(path, units=units)[0])


def run_electric(unit_system: str) -> dict[str, float]:
    prob = om.Problem()
    prob.model = mp = MPpropulsor(unit_system=unit_system)
    prob.setup()

    prob.set_val('design.fc.alt', 10000, units='m')
    prob.set_val('design.fc.MN', 0.8)
    prob.set_val('design.inlet.MN', 0.6)
    prob.set_val('design.fan.PR', 1.2)
    prob.set_val('pwr_target', -3486.657, units='hp')
    prob.set_val('design.fan.eff', 0.96)
    prob.set_val('design.balance.W', 200.0, units='lbm/s')

    for pt in mp.od_pts:
        prob[f'{pt}.fan.PR'] = 1.2
        prob.set_val(f'{pt}.balance.W', 406.790, units='lbm/s')
        prob[f'{pt}.balance.Nmech'] = 1.0

    prob.set_solver_print(level=-1)
    prob.run_model()

    point = 'design'
    return {
        'Fn': _s(prob, f'{point}.perf.Fn', 'N' if unit_system == 'SI' else 'lbf'),
        'OPR': _s(prob, f'{point}.perf.OPR'),
        'W': _s(prob, f'{point}.inlet.Fl_O:stat:W', 'kg/s' if unit_system == 'SI' else 'lbm/s'),
        'Tt': _s(prob, f'{point}.fan.Fl_O:tot:T', 'degK' if unit_system == 'SI' else 'degR'),
        'Pt': _s(prob, f'{point}.fan.Fl_O:tot:P', 'Pa' if unit_system == 'SI' else 'lbf/inch**2'),
    }


def run_simple_turbojet(unit_system: str) -> dict[str, float]:
    prob = om.Problem()
    prob.model = mp = MPTurbojet(unit_system=unit_system)
    prob.setup(check=False)

    prob.set_val('DESIGN.fc.alt', 0, units='ft')
    prob.set_val('DESIGN.fc.MN', 0.000001)
    prob.set_val('DESIGN.balance.Fn_target', 11800.0, units='lbf')
    prob.set_val('DESIGN.balance.T4_target', 2370.0, units='degR')
    prob.set_val('DESIGN.comp.PR', 13.5)
    prob.set_val('DESIGN.comp.eff', 0.83)
    prob.set_val('DESIGN.turb.eff', 0.86)

    prob['DESIGN.balance.FAR'] = 0.0175506829934
    prob.set_val('DESIGN.balance.W', 168.453135137, units='lbm/s')
    prob['DESIGN.balance.turb_PR'] = 4.46138725662
    prob.set_val('DESIGN.fc.balance.Pt', 14.6955113159, units='psi')
    prob.set_val('DESIGN.fc.balance.Tt', 518.665288153, units='degR')

    for pt in mp.od_pts:
        prob.set_val(f'{pt}.balance.W', 166.073, units='lbm/s')
        prob[f'{pt}.balance.FAR'] = 0.01680
        prob.set_val(f'{pt}.balance.Nmech', 8197.38, units='rpm')
        prob.set_val(f'{pt}.fc.balance.Pt', 15.703, units='psi')
        prob.set_val(f'{pt}.fc.balance.Tt', 558.31, units='degR')
        prob[f'{pt}.turb.PR'] = 4.6690

    prob.set_solver_print(level=-1)
    prob.run_model()

    point = 'DESIGN'
    return {
        'Fn': _s(prob, f'{point}.perf.Fn', 'N' if unit_system == 'SI' else 'lbf'),
        'TSFC': _s(prob, f'{point}.perf.TSFC'),
        'OPR': _s(prob, f'{point}.perf.OPR'),
        'W': _s(prob, f'{point}.inlet.Fl_O:stat:W', 'kg/s' if unit_system == 'SI' else 'lbm/s'),
        'Tt': _s(prob, f'{point}.burner.Fl_O:tot:T', 'degK' if unit_system == 'SI' else 'degR'),
        'Pt': _s(prob, f'{point}.comp.Fl_O:tot:P', 'Pa' if unit_system == 'SI' else 'lbf/inch**2'),
    }


def run_multi_spool(unit_system: str) -> dict[str, float]:
    prob = om.Problem()
    prob.model = mp = MPMultiSpool(unit_system=unit_system)
    prob.setup()

    prob.set_val('DESIGN.fc.alt', 28000.0, units='ft')
    prob.set_val('DESIGN.fc.MN', 0.5)
    prob.set_val('DESIGN.balance.rhs:FAR', 2740.0, units='degR')
    prob.set_val('DESIGN.balance.rhs:W', 1.1)
    prob.set_val('DESIGN.lpc.PR', 5.000)
    prob.set_val('DESIGN.lpc.eff', 0.8900)
    prob.set_val('DESIGN.hpc_axi.PR', 3.0)
    prob.set_val('DESIGN.hpc_axi.eff', 0.8900)
    prob.set_val('DESIGN.hpc_centri.PR', 2.7)
    prob.set_val('DESIGN.hpc_centri.eff', 0.8800)
    prob.set_val('DESIGN.hpt.eff', 0.89)
    prob.set_val('DESIGN.lpt.eff', 0.9)
    prob.set_val('DESIGN.pt.eff', 0.85)

    prob['DESIGN.balance.FAR'] = 0.02261
    prob.set_val('DESIGN.balance.W', 10.76, units='lbm/s')
    prob['DESIGN.balance.hpt_PR'] = 4.233
    prob['DESIGN.balance.lpt_PR'] = 1.979
    prob['DESIGN.balance.pt_PR'] = 4.919
    prob.set_val('DESIGN.fc.balance.Pt', 5.666, units='psi')
    prob.set_val('DESIGN.fc.balance.Tt', 440.0, units='degR')

    for pt in mp.od_pts:
        prob[f'{pt}.balance.FAR'] = 0.02135
        prob.set_val(f'{pt}.balance.W', 10.775, units='lbm/s')
        prob.set_val(f'{pt}.balance.HP_Nmech', 14800.000, units='rpm')
        prob.set_val(f'{pt}.balance.IP_Nmech', 12000.000, units='rpm')
        prob[f'{pt}.hpt.PR'] = 4.233
        prob[f'{pt}.lpt.PR'] = 1.979
        prob[f'{pt}.pt.PR'] = 4.919
        prob.set_val(f'{pt}.fc.balance.Pt', 5.666, units='psi')
        prob.set_val(f'{pt}.fc.balance.Tt', 440.0, units='degR')
        prob[f'{pt}.nozzle.PR'] = 1.1

    prob.set_solver_print(level=-1)
    prob.run_model()

    point = 'DESIGN'
    return {
        'Fn': _s(prob, f'{point}.perf.Fn', 'N' if unit_system == 'SI' else 'lbf'),
        'PSFC': _s(prob, f'{point}.perf.PSFC'),
        'OPR': _s(prob, f'{point}.perf.OPR'),
        'W': _s(prob, f'{point}.inlet.Fl_O:stat:W', 'kg/s' if unit_system == 'SI' else 'lbm/s'),
        'Tt': _s(prob, f'{point}.burner.Fl_O:tot:T', 'degK' if unit_system == 'SI' else 'degR'),
        'Pt': _s(prob, f'{point}.hpc_centri.Fl_O:tot:P', 'Pa' if unit_system == 'SI' else 'lbf/inch**2'),
    }


def _fmt(v: float) -> str:
    return f"{v:.6g}"


def main() -> None:
    runners = {
        'electric_propulsor.py': run_electric,
        'simple_turbojet.py': run_simple_turbojet,
        'multi_spool_turboshaft.py': run_multi_spool,
    }
    results: dict[tuple[str, str], dict[str, float]] = {}
    for example, runner in runners.items():
        for unit_system in ('ENG', 'SI'):
            results[(example, unit_system)] = runner(unit_system)

    out = Path(__file__).resolve().parents[1] / 'docs' / 'units_examples_report.md'
    lines = [
        '# Units Example Matrix',
        '',
        'Generated by `example_cycles/run_units_matrix.py`.',
        '',
        '| Example | Unit System | Fn | OPR | W | Tt | Pt |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for example in runners:
        for unit_system in ('ENG', 'SI'):
            row = results[(example, unit_system)]
            lines.append(
                f"| `{example}` | {unit_system} | {_fmt(row['Fn'])} | {_fmt(row['OPR'])} | {_fmt(row['W'])} | {_fmt(row['Tt'])} | {_fmt(row['Pt'])} |"
            )
    lines.append('')
    lines.append('## Extra Metrics')
    lines.append('')
    lines.append('| Example | Unit System | Metric | Value |')
    lines.append('|---|---:|---|---:|')
    for example in runners:
        for unit_system in ('ENG', 'SI'):
            row = results[(example, unit_system)]
            for metric in ('TSFC', 'PSFC'):
                if metric in row:
                    lines.append(f"| `{example}` | {unit_system} | {metric} | {_fmt(row[metric])} |")

    out.write_text('\n'.join(lines) + '\n')
    print(f"Wrote {out}")


if __name__ == '__main__':
    main()
