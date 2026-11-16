"""Presentation renderer for planner trajectories (no solver dependency)."""
from pathlib import Path
import json
import math

import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
import numpy as np

BG = '#0b1220'
PANEL = '#111e30'
INK = '#edf4ff'
MUTED = '#91a7c1'
COLORS = ('#55dcca', '#ffbd69', '#a99bff', '#6bbcff', '#ff829c', '#c7e882')
MARKERS = ('o', 's', '^', 'D', 'P', 'X')


def cells(value):
    """Normalize both legacy single-cell and multi-cell workspace regions."""
    array = np.asarray(value, dtype=float)
    return array.reshape(-1, 2)


class Trajectory:
    """Random-access playback; drawing the same frame never advances time."""
    def __init__(self, paths, times):
        if not paths or any(len(path) == 0 for path in paths.values()):
            raise ValueError('At least one robot with a nonempty path is required.')
        self.paths = {robot: cells(path) for robot, path in paths.items()}
        self.times = {}
        for robot, path in self.paths.items():
            start, end = times[robot]
            if start != int(start) or end != int(end) or not 0 <= start <= end:
                raise ValueError('Prefix/suffix boundaries must be ordered, nonnegative integers.')
            start, end = int(start), int(end)
            if start != end and (end >= len(path) or not np.array_equal(path[start], path[end])):
                raise ValueError('A repeating suffix must end at its starting cell, inside the path.')
            self.times[robot] = start, end
        self.horizon = max(
            max(len(path) - 1, 2 * end - start) if start < end else len(path) - 1
            for robot, path in self.paths.items() for start, end in [self.times[robot]]
        )

    def position(self, robot, step):
        path = self.paths[robot]
        step = max(0., float(step))
        start, end = self.times[robot]
        if step >= len(path) - 1:
            if start == end:
                return path[-1].copy()
            step = start + (step - start) % (end - start)
        index = int(math.floor(step))
        fraction = step - index
        return path[index] * (1 - fraction) + path[min(index + 1, len(path) - 1)] * fraction

    def positions(self, step):
        return {robot: self.position(robot, step) for robot in self.paths}


def satisfied_ap(workspace, positions, ap):
    """Current conjunctions only; this is not a full temporal-logic verifier."""
    result = {}
    for conjunction in ap:
        matches = {}
        for region, kind, count, *rest in conjunction:
            members = [robot[1] + 1 for robot, point in positions.items()
                       if robot[0] == kind and np.any(np.all(
                           np.isclose(cells(workspace.regions[region]), point, atol=1e-8, rtol=0), axis=1))]
            if len(members) < count:
                break
            matches[(region, kind)] = members
        else:
            result.update(matches)
    return result


def plot_workspace_helper(ax, objects, obj_label):
    for index, (name, value) in enumerate(objects.items()):
        if name.startswith('r'):
            continue
        points = cells(value)
        if not len(points):
            continue
        region = obj_label == 'region'
        color = COLORS[index % len(COLORS)] if region else '#34465b'
        patches = [Rectangle((x + .04, y + .04), .92, .92) for x, y in points]
        ax.add_collection(PatchCollection(patches, facecolors=color,
                          edgecolors=color if region else '#506177',
                          linewidths=.6, alpha=.17 if region else .85, zorder=1))
        if region:
            # Anchor to an actual cell, including for nonrectangular regions.
            anchor = points[np.argmax(points[:, 1])]
            ax.text(anchor[0] + .12, anchor[1] + .82, name.upper(),
                    color=color, fontsize=8, weight='bold', zorder=3,
                    bbox=dict(facecolor=BG, edgecolor='none', alpha=.8, pad=2))


def plot_workspace(workspace, ax):
    ax.set_facecolor(PANEL)
    ax.set(xlim=(0, workspace.width), ylim=(0, workspace.length), aspect='equal')
    ax.set_xticks(np.arange(workspace.width + 1), minor=True)
    ax.set_yticks(np.arange(workspace.length + 1), minor=True)
    stride = max(1, int(math.ceil(max(workspace.width, workspace.length) / 10)))
    ax.set_xticks(np.arange(0, workspace.width + 1, stride))
    ax.set_yticks(np.arange(0, workspace.length + 1, stride))
    ax.grid(which='both', color='#294057', linewidth=.5, alpha=.45)
    ax.tick_params(which='both', length=0, labelsize=8, colors=MUTED, pad=8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color('#294057')
    plot_workspace_helper(ax, workspace.regions, 'region')
    plot_workspace_helper(ax, workspace.obstacles, 'obstacle')


class Presentation:
    def __init__(self, workspace, paths, times, ap=(), *, title='Multi-robot coordination',
                 subtitle='LTL task allocation  /  trajectory playback', fps=30, steps_per_second=2,
                 mission=None):
        if fps <= 0 or steps_per_second <= 0:
            raise ValueError('Frame rate and playback speed must be positive.')
        self.workspace, self.ap = workspace, ap
        self.trajectory = Trajectory(paths, times)
        self.mission_view = None
        self.fps, self.speed = fps, steps_per_second
        self.frame_count = max(2, math.ceil(self.trajectory.horizon / self.speed * fps) + 1)
        self.step, self.paused = 0., False
        self.fig = plt.figure(figsize=(16, 9), facecolor=BG)
        self.ax = self.fig.add_axes([.055, .12, .60, .80])
        plot_workspace(workspace, self.ax)
        self.panel = self.fig.add_axes([.705, .12, .25, .80], facecolor=PANEL)
        self.panel.set(xticks=[], yticks=[], xlim=(0, 1), ylim=(0, 1))
        for spine in self.panel.spines.values():
            spine.set_visible(False)
        self.text(.07, .94, 'EXECUTION MONITOR', size=10, color=MUTED)
        self.clock = self.text(.07, .835, '', size=30)
        self.text(.07, .775, 'DISCRETE PLAN STEP', size=8, color=MUTED)
        types = sorted({r[0] for r in paths})
        self.type_colors = {kind: COLORS[i % len(COLORS)] for i, kind in enumerate(types)}
        self.text(.07, .69, f'{len(paths):02d} ROBOTS     /     {len(types):02d} TYPES', size=11)
        self.groups, self.trails, self.labels = [], {}, {}
        self.show_labels = len(paths) <= 24
        marker_size = max(70, min(190, 13000 / max(workspace.width, workspace.length) ** 2))
        for index, kind in enumerate(types):
            color = self.type_colors[kind]
            robots = [r for r in paths if r[0] == kind]
            self.panel.scatter([.09], [.62 - index * min(.05, .23 / len(types))],
                               s=65, c=color, marker=MARKERS[index % len(MARKERS)])
            self.text(.15, .62 - index * min(.05, .23 / len(types)),
                      f'Type {kind}  /  {len(robots)} robots', size=10)
            halo = self.ax.scatter([], [], s=marker_size * 2.4, color=color, alpha=.10, zorder=5)
            body = self.ax.scatter([], [], s=marker_size, color=color,
                                   marker=MARKERS[index % len(MARKERS)],
                                   edgecolors=INK, linewidths=1., zorder=6)
            self.groups.append((robots, halo, body))
        for robot in paths:
            color = self.type_colors[robot[0]]
            self.trails[robot], = self.ax.plot([], [], color=color, linewidth=2.2,
                                             alpha=.55, solid_capstyle='round', zorder=4)
            if self.show_labels:
                self.labels[robot] = self.ax.text(0, 0, str(robot[1] + 1), ha='center',
                                                va='center', color=BG, weight='bold', fontsize=7, zorder=7)
        self.text(.07, .32, 'CURRENT REGION OCCUPANCY', size=9, color=MUTED)
        self.occupancy = self.text(.07, .265, '', size=10, va='top')
        self.text(.07, .055, 'Sampled at the last integer plan step', size=8, color=MUTED)
        self.status = self.fig.text(.055, .075, '', color=MUTED, fontsize=10, visible=False)
        self.controls = self.fig.text(.955, .075, 'SPACE  pause     ← / →  step     R  restart',
                                      color=MUTED, fontsize=9, ha='right', visible=False)
        progress_ax = self.fig.add_axes([.055, .065, .9, .006], facecolor='#24364b')
        progress_ax.set(xticks=[], yticks=[], xlim=(0, 1), ylim=(0, 1))
        for spine in progress_ax.spines.values():
            spine.set_visible(False)
        self.progress = Rectangle((0, 0), 0, 1, facecolor=COLORS[0])
        progress_ax.add_patch(self.progress)
        if mission is not None:
            if mission.get('case') == 1:
                from .ltl_progress import Case1Monitor
                from .mission_panel import Case1Panel
                self.mission_view = Case1Panel(self, Case1Monitor(workspace, self.trajectory, mission))
            else:
                from .run_panel import RunMonitor, RunPanel
                self.mission_view = RunPanel(self, RunMonitor(workspace, self.trajectory, mission))
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.draw(0)

    def text(self, x, y, value, size=12, color=INK, va='center'):
        return self.panel.text(x, y, value, fontsize=size, color=color, va=va,
                               fontfamily='DejaVu Sans')

    def draw(self, step):
        self.step = min(max(0., step), self.trajectory.horizon)
        positions = self.trajectory.positions(self.step)
        for robots, halo, body in self.groups:
            offsets = np.array([positions[r] + .5 for r in robots])
            halo.set_offsets(offsets)
            body.set_offsets(offsets)
        for robot, line in self.trails.items():
            # Include integer corners so trails cannot cut across obstacles.
            start = max(0., self.step - 4)
            samples = [start] + list(range(math.ceil(start), math.floor(self.step) + 1)) + [self.step]
            points = np.array([self.trajectory.position(robot, t) + .5 for t in samples])
            line.set_data(points[:, 0], points[:, 1])
            if robot in self.labels:
                self.labels[robot].set_position(positions[robot] + .5)
        discrete = self.trajectory.positions(math.floor(self.step + 1e-9))
        occupied = []
        for region, value in self.workspace.regions.items():
            if region.startswith('r'):
                continue
            members = [r for r, p in discrete.items()
                       if np.any(np.all(np.isclose(cells(value), p, rtol=0, atol=1e-8), axis=1))]
            if members:
                occupied.append(f'{region.upper():<5}   {len(members)} robot' + ('s' if len(members) != 1 else ''))
        self.occupancy.set_text('\n'.join(occupied[:5]) +
                                (f'\n+ {len(occupied) - 5} more regions' if len(occupied) > 5 else '')
                                if occupied else 'Robots in transit')
        self.clock.set_text(f'{self.step:05.1f} / {self.trajectory.horizon}')
        self.clock.set_fontsize(24 if self.trajectory.horizon >= 100 else 30)
        self.progress.set_width(self.step / max(1, self.trajectory.horizon))
        active = satisfied_ap(self.workspace, discrete, self.ap)
        state = 'PAUSED' if self.paused else ('COMPLETE' if self.step >= self.trajectory.horizon else 'PLAYBACK')
        suffix = f'  •  {len(active)} active region/type conditions' if self.ap else ''
        self.status.set_text(f'{state}   /   {self.speed:g} plan steps per second{suffix}')
        if self.mission_view is not None:
            self.mission_view.draw(self.step, positions)
        return [self.progress, self.clock, self.occupancy, self.status]

    def on_key(self, event):
        if event.key == ' ':
            self.paused = not self.paused
        elif event.key == 'r':
            self.step = 0
        elif event.key in ('left', 'right'):
            self.paused = True
            self.step += -1 if event.key == 'left' else 1
        elif event.key in ('n', 'p') and self.mission_view is not None:
            steps = sorted({e.step for e in self.mission_view.monitor.events})
            candidates = [t for t in steps if t > self.step] if event.key == 'n' else [t for t in steps if t < self.step]
            if candidates:
                self.step = min(candidates) if event.key == 'n' else max(candidates)
            self.paused = True
        self.draw(self.step)
        self.fig.canvas.draw_idle()

    def show(self):
        def tick(_):
            self.draw(self.step if self.paused else min(self.trajectory.horizon, self.step + self.speed / self.fps))
        self.ani = animation.FuncAnimation(self.fig, tick, interval=1000 / self.fps,
                                          cache_frame_data=False)
        plt.show()

    def save(self, output, *, dpi=120):
        controls = self.controls.get_text()
        self.controls.set_text('LTL TASK ALLOCATION  /  TRAJECTORY REPLAY')
        try:
            return self._save(output, dpi=dpi)
        finally:
            self.controls.set_text(controls)

    def _save(self, output, *, dpi=120):
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix.lower() == '.png':
            self.fig.savefig(output, dpi=dpi, facecolor=BG)
            return output
        if output.suffix.lower() not in ('.mp4', '.gif'):
            raise ValueError('Output must be .png, .mp4, or .gif.')
        if output.suffix.lower() == '.mp4' and not animation.writers.is_available('ffmpeg'):
            try:
                import imageio_ffmpeg
                plt.rcParams['animation.ffmpeg_path'] = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError as error:
                raise RuntimeError('MP4 export requires FFmpeg or imageio-ffmpeg. '
                                   'Install requirements-demo.txt or use a .gif output.') from error
        movie = animation.FuncAnimation(
            self.fig, lambda frame: self.draw(min(frame * self.speed / self.fps, self.trajectory.horizon)),
            init_func=lambda: self.draw(0), frames=self.frame_count, interval=1000 / self.fps, blit=False)
        writer = animation.FFMpegWriter(fps=self.fps, codec='libx264',
                                       extra_args=['-pix_fmt', 'yuv420p', '-crf', '19']) if output.suffix.lower() == '.mp4' else animation.PillowWriter(fps=self.fps)
        movie.save(str(output), writer=writer, dpi=dpi)
        return output


def save_replay(output, workspace, paths, times, ap, title, subtitle, mission=None):
    """Portable JSON, safe to load without unpickling workspace/solver objects."""
    data = dict(version=1, title=title, subtitle=subtitle, width=workspace.width,
                length=workspace.length, regions={k: cells(v).tolist() for k, v in workspace.regions.items()},
                obstacles={k: cells(v).tolist() for k, v in workspace.obstacles.items()},
                robots=[dict(id=list(r), path=cells(p).tolist(), timing=list(map(int, times[r])))
                        for r, p in paths.items()], ap=ap)
    if mission is not None:
        data['mission'] = mission
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2), encoding='utf-8')


def vis(case, workspace, robot_path, robot_pre_suf_time, ap, *, output=None, fps=30,
        steps_per_second=2, show=False, title=None, mission=None):
    """Drop-in planner entry point; export a video, poster and reusable replay."""
    output = Path(output or f'data/mapp_case{case}.mp4')
    title = title or f'Multi-robot coordination / Case {case}'
    subtitle = 'LTL task allocation  /  planner trajectory playback'
    if case == 1 and mission is None:
        mission = {'case': 1}
    with plt.rc_context({'text.usetex': False, 'font.family': 'DejaVu Sans'}):
        view = Presentation(workspace, robot_path, robot_pre_suf_time, ap, title=title,
                            subtitle=subtitle, fps=fps, steps_per_second=steps_per_second, mission=mission)
        try:
            save_replay(output.with_suffix('.json'), workspace, robot_path, robot_pre_suf_time, ap, title, subtitle, mission)
            view.save(output.with_suffix('.png'))
            if output.suffix.lower() != '.png':
                view.save(output)
            if show:
                view.show()
        finally:
            plt.close(view.fig)
    return output
