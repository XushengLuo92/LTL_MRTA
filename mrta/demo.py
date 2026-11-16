"""Run a presentation or export a saved planner replay without Gurobi."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace


def load_replay(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('version') != 1:
        raise ValueError('Unsupported replay version; expected version 1.')
    workspace = SimpleNamespace(width=data['width'], length=data['length'],
                                regions=data['regions'], obstacles=data['obstacles'])
    paths = {tuple(r['id']): r['path'] for r in data['robots']}
    times = {tuple(r['id']): r['timing'] for r in data['robots']}
    return workspace, paths, times, data.get('ap', []), data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', type=Path, default=Path(__file__).resolve().parent.parent / 'demo' / 'case1.json')
    parser.add_argument('--case', type=int, choices=[1], help='Enable the Case 1 monitor on an older replay.')
    parser.add_argument('--output', type=Path, help='Export .mp4, .gif or .png; omit for interactive playback.')
    parser.add_argument('--fps', type=int, default=30)
    parser.add_argument('--speed', type=float, default=2, help='Plan steps per second.')
    parser.add_argument('--step', type=float, default=0, help='Initial step / PNG snapshot step.')
    parser.add_argument('--dpi', type=int, default=120)
    args = parser.parse_args()
    if args.fps <= 0 or args.speed <= 0 or args.dpi <= 0:
        parser.error('--fps, --speed and --dpi must be positive.')
    import matplotlib
    if args.output:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from .vis import Presentation
    workspace, paths, times, ap, data = load_replay(args.replay)
    with plt.rc_context({'text.usetex': False, 'font.family': 'DejaVu Sans'}):
        view = Presentation(workspace, paths, times, ap, title=data['title'],
                            subtitle=data['subtitle'], fps=args.fps, steps_per_second=args.speed,
                            mission=data.get('mission') or ({'case': args.case} if args.case else None))
        try:
            view.draw(args.step)
            if args.output:
                view.save(args.output, dpi=args.dpi)
                print(f'Saved {args.output.resolve()}')
            else:
                view.show()
        finally:
            plt.close(view.fig)


if __name__ == '__main__':
    main()
