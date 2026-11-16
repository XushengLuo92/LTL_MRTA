"""Export the two shared workspace layouts from the published demo replays."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mrta.demo import load_replay
from mrta.vis import BG, plot_workspace


def layout(workspace):
    """Ignore per-robot helper regions when comparing physical layouts."""
    return (
        workspace.width,
        workspace.length,
        *({name: sorted(map(tuple, cells)) for name, cells in objects.items()
           if not name.startswith('r')}
          for objects in (workspace.regions, workspace.obstacles)),
    )


def main():
    folder = ROOT / 'demo/generated'
    for cases, name in [(range(1, 9), 'workspace_cases_01_08'),
                        (range(9, 11), 'workspace_cases_09_10')]:
        workspace, *_ = load_replay(folder / f'case_{cases.start:02d}.json')
        for case in cases:
            other, *_ = load_replay(folder / f'case_{case:02d}.json')
            if layout(workspace) != layout(other):
                raise ValueError(f'Case {case} does not share the expected layout')
        with plt.rc_context({'text.usetex': False, 'font.family': 'DejaVu Sans'}):
            fig, ax = plt.subplots(figsize=(7, 7), facecolor=BG)
            try:
                plot_workspace(workspace, ax)
                for label in ax.texts:
                    label.set_fontsize(10)
                fig.subplots_adjust(left=.065, right=.985, bottom=.065, top=.985)
                output = folder / f'{name}.png'
                fig.savefig(output, dpi=160, facecolor=BG)
                print(f'Saved {output}')
            finally:
                plt.close(fig)


if __name__ == '__main__':
    main()
