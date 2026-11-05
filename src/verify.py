"""Verify that repeated fixed-paper-method outputs are byte-identical."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import yaml
from .run_experiment import evaluate, write_json


def verify(reports='reports', workers=6):
    reports = Path(reports)
    manifest = json.loads((reports/'dataset_manifest.json').read_text())
    original = reports/'paper_protocol'
    cfg = yaml.safe_load((original/'config.yaml').read_text())
    repeat = reports/'verification_repeat'
    evaluate(manifest, cfg['pipeline'], repeat, reports/'cache', workers, cfg['backend'])
    checks = {}
    for filename in ('per_patient.csv', 'per_slice.csv', 'summary.json'):
        a, b = (original/filename).read_bytes(), (repeat/filename).read_bytes()
        if a != b:
            raise ValueError(f'Nondeterministic output: {filename}')
        checks[filename] = dict(identical=True, sha256=hashlib.sha256(a).hexdigest())
    write_json(reports/'verification.json', dict(determinism=checks, method='Fixed paper parameters for every patient'))
    shutil.rmtree(repeat)
    print('Fixed paper method: repeated CSV and summary outputs are byte-identical', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reports', default='reports')
    parser.add_argument('--workers', type=int, default=6)
    args = parser.parse_args()
    verify(args.reports, args.workers)
