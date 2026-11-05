"""Cross-platform entry point: python run.py all --workers 6."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
PHASES = {
    'audit': 'src.io_chaos',
    'test': 'unittest',
    'evaluate': 'src.run_experiment',
    'diagnostics': 'src.diagnostics',
    'figures': 'src.make_figures',
    'visualization': 'src.export_segmentations',
    'integrity': 'src.check_integrity',
    'verify': 'src.verify',
    'report': 'src.report',
}
WORKER_PHASES = {'evaluate', 'visualization', 'integrity', 'verify'}


def phase_command(phase, workers=6, data=None, archive=False):
    """Construct an argument list, avoiding shell-dependent quoting and commands."""
    args = [sys.executable, '-m', PHASES[phase]]
    if phase == 'test':
        args += ['discover', '-s', 'tests', '-v']
    if phase in WORKER_PHASES:
        args += ['--workers', str(workers)]
    if phase == 'visualization':
        args += ['--out', 'visualization']
        if not archive:
            args += ['--no-archive']
    if phase in {'audit', 'evaluate'} and data:
        args += ['--data', str(Path(data).expanduser().resolve())]
    return args


def main():
    parser = argparse.ArgumentParser(description='Run the CT paper implementation on Windows, macOS or Linux.')
    parser.add_argument('phase', choices=['all', *PHASES], nargs='?', default='all')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--data', help='Labelled CHAOS CT directory, if not using the default DATASET layout')
    parser.add_argument('--archive', action='store_true', help='Also create visualization.zip')
    args = parser.parse_args()
    if args.workers < 1:
        parser.error('--workers must be positive')
    env = os.environ.copy()
    env.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'liver-hu-matplotlib'))
    env.setdefault('OPENBLAS_NUM_THREADS', '1')
    env.setdefault('OMP_NUM_THREADS', '1')
    phases = list(PHASES) if args.phase == 'all' else [args.phase]
    for phase in phases:
        print(f'Running {phase}...', flush=True)
        # The all workflow audits once before any patient data is processed.
        data = args.data if phase == 'audit' or (args.phase != 'all' and phase == 'evaluate') else None
        subprocess.run(phase_command(phase, args.workers, data, args.archive), cwd=ROOT, env=env, check=True)


if __name__ == '__main__':
    main()
