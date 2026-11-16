"""Run real planners and save per-case replay files/logs without video overhead."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=int, nargs='+', default=list(range(2, 11)))
    parser.add_argument('--output-dir', type=Path, default=Path('data/all_cases'))
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--robots', type=int, default=12, help='Team size for cases 9 and 10 (multiple of four).')
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    manifest = args.output_dir / 'batch-planning.json'
    prior = {row['case']: row for row in json.loads(manifest.read_text())} if manifest.exists() else {}
    for case in args.cases:
        module = 'case.case1' if case <= 2 else 'case.case2' if case <= 8 else 'case.case3'
        command = [sys.executable, '-u', '-m', module, f'--case={case}', '--partial_or_full=f',
                   '--planning-mode=simultaneous', f'--seed={args.seed}', f'--robot={args.robots}',
                   '--only_first', '--loop', '--replay-only', '--print', '--output-dir', str(args.output_dir)]
        logfile = args.output_dir / f'case_{case:02d}.log'
        replay = args.output_dir / f'case_{case:02d}.json'
        start = time.monotonic()
        print(f'Running Case {case}', flush=True)
        with logfile.open('w') as log:
            try:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                        env={**os.environ, 'PYTHONHASHSEED': '0', 'MPLBACKEND': 'Agg'}, timeout=args.timeout)
                status = 'planned' if result.returncode == 0 and replay.exists() and replay.stat().st_mtime >= time.time() - (time.monotonic()-start) - 1 else 'failed'
                code = result.returncode
            except subprocess.TimeoutExpired:
                status, code = 'timeout', None
        row = {'case': case, 'status': status, 'seconds': round(time.monotonic()-start, 2),
               'exit_code': code, 'seed': args.seed, 'robots': args.robots if case >= 9 else 5,
               'command': command, 'log': str(logfile)}
        results.append(row)
        prior[case] = row
        manifest.write_text(json.dumps(sorted(prior.values(), key=lambda row: row['case']), indent=2)+'\n')
        print(json.dumps(row), flush=True)
    return int(any(r['status'] != 'planned' for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
