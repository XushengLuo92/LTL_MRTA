"""Linked mission cards, region overlays and event navigation for Case 1."""
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle, FancyBboxPatch

from .vis import BG, PANEL, INK, MUTED, COLORS, cells

GOOD, AMBER, BAD = COLORS[0], COLORS[1], '#ff829c'


class Case1Panel:
    def __init__(self, view, monitor):
        self.view, self.monitor = view, monitor
        view.panel.set_visible(False)
        view.ax.set_position([.045, .19, .475, .72])
        view.ax.tick_params(labelbottom=False)
        self.ax = view.fig.add_axes([.565, .19, .39, .72], facecolor=PANEL)
        view.progress.axes.set_position([.055, .04, .9, .006])
        self.ax.set(xlim=(0, 1), ylim=(0, 1), xticks=[], yticks=[])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.label(.04, .955, 'CASE 1 / LTL MISSION', 11, MUTED)
        self.clock = self.label(.96, .955, '', 10, MUTED, ha='right')
        self.label(.04, .894, r'$\diamond((A\wedge\neg D)\wedge\diamond B)\ \wedge\ \diamond C\ \wedge\ (\neg D\ U\ C)$', 15)
        self.label(.04, .837, 'A / pair at L2     B / same pair at L3     C / Type 2 at L4', 9, MUTED)
        self.label(.04, .795, 'D / any two Type 1 robots at L3', 9, MUTED)
        self.cards = []
        for y, title, symbol in [(.56, 'Visit L2 together', 'A'), (.38, 'Release the L3 restriction', 'C'),
                                  (.20, 'Same pair visits L3', 'B')]:
            card = FancyBboxPatch((.035, y), .93, .155, boxstyle='round,pad=0.008,rounding_size=0.012',
                                  facecolor=BG, edgecolor='#294057', linewidth=1.1)
            self.ax.add_patch(card)
            self.label(.065, y+.108, f'{symbol}   {title}', 12)
            badge = self.label(.935, y+.108, '', 9, ha='right')
            detail = self.label(.065, y+.047, '', 9, MUTED)
            self.cards.append((card, badge, detail))
        self.verdict = self.label(.04, .12, '', 12, visible=False)
        self.now = self.label(.04, .055, '', 9, MUTED, visible=False)
        self.overlays = {}
        for region in ('l2', 'l3', 'l4'):
            overlay = PatchCollection([Rectangle((x+.02, y+.02), .96, .96) for x, y in cells(view.workspace.regions[region])],
                                      facecolors='none', edgecolors=AMBER, linewidths=1.5, zorder=2)
            view.ax.add_collection(overlay)
            self.overlays[region] = overlay
        self.team_ring = view.ax.scatter([], [], s=330, facecolors='none', edgecolors=INK,
                                         linewidths=1.4, zorder=8)
        self.banner = view.fig.text(.055, .145, '', color=AMBER, fontsize=11, weight='bold')
        view.fig.text(.055, .94, '●  TYPE 1', color=COLORS[0], fontsize=9)
        view.fig.text(.12, .94, '■  TYPE 2', color=COLORS[1], fontsize=9)
        self.timeline = view.fig.add_axes([.075, .075, .86, .045], facecolor=BG)
        self.timeline.set(xlim=(-.5, max(1, view.trajectory.horizon)+.5), ylim=(0, 1))
        self.timeline.axis('off')
        self.timeline.plot([0, max(1, view.trajectory.horizon)], [.45, .45], color='#294057', lw=2)
        self.cursor = self.timeline.axvline(0, color=INK, linewidth=1, alpha=.65)
        self.event_artists = []
        for index, event in enumerate(monitor.events):
            marker, = self.timeline.plot([event.step], [.45], marker='o', ms=7, color=MUTED)
            label = self.timeline.text(event.step, .82 if index % 2 == 0 else .02,
                                       f'{event.kind} · {event.step}', color=MUTED, fontsize=9,
                                       ha='center', va='center')
            self.event_artists.append((event, marker, label))
        view.fig.canvas.mpl_connect('button_press_event', self.seek)
        view.controls.set_text('SPACE pause   ← / → step   N / P event   R restart')

    def label(self, x, y, text, size=10, color=INK, **kwargs):
        return self.ax.text(x, y, text, color=color, fontsize=size, va='center', **kwargs)

    def seek(self, event):
        if event.inaxes is self.timeline and event.xdata is not None:
            self.view.paused = True
            self.view.draw(round(event.xdata))
            self.view.fig.canvas.draw_idle()

    def draw(self, step, positions):
        state = self.monitor.at(step)
        self.clock.set_text(f'STEP {step:04.1f} / {self.view.trajectory.horizon}')
        team = state.team
        team_name = ' + '.join(f'R{r[1]+1}' for r in team) or 'any eligible pair'
        a_count = len(set(team).intersection(state.l2)) if team else len(state.l2)
        b_count = len(set(team).intersection(state.l3)) if team else len(state.l3)
        a_status = f'WITNESSED · {state.a_step}' if state.a_step is not None else 'ACTIVE'
        a_detail = f'Type 1 / {team_name}   ·   at L2 now: {a_count}/2'
        if state.a_step is None and len(state.l3) >= 2:
            a_detail = 'Waiting: A also requires fewer than two Type 1 in L3.'
        c_status = f'RELEASED · {state.release_step}' if state.release_step is not None else 'RESTRICTED'
        c_detail = 'Type 2 visit remembered, even after leaving L4.' if state.release_step is not None else 'Keep Type 1 count at L3 below 2 until Type 2 reaches L4.'
        b_status = f'WITNESSED · {state.b_step}' if state.b_step is not None else (
            'WAITING FOR A' if state.a_step is None else ('WAITING FOR C' if state.release_step is None else 'ACTIVE'))
        b_detail = f'Type 1 / {team_name}   ·   at L3 now: {b_count}/2'
        rows = [(a_status, a_detail, state.a_step is not None),
                (c_status, c_detail, state.release_step is not None),
                (b_status, b_detail, state.b_step is not None)]
        for (card, badge, detail), (status, text, done) in zip(self.cards, rows):
            color = GOOD if done else AMBER
            card.set_edgecolor(color)
            badge.set_text(status)
            badge.set_color(color)
            detail.set_text(text)
        if state.violation_step is not None:
            card, badge, detail = self.cards[1]
            card.set_edgecolor(BAD)
            badge.set_text(f'VIOLATED · {state.violation_step}')
            badge.set_color(BAD)
            detail.set_text('Later release cannot undo the earlier until violation.')
        self.verdict.set_text('CASE 1  /  ' + state.state)
        self.verdict.set_color(BAD if state.violation_step is not None else GOOD if state.satisfied else INK)
        self.now.set_text(f'NOW:  L2 / Type 1 = {len(state.l2)}     L3 / Type 1 = {len(state.l3)}     L4 / Type 2 = {len(state.l4)}')
        for region, done in [('l2', state.a_step is not None), ('l4', state.release_step is not None),
                             ('l3', state.b_step is not None)]:
            self.overlays[region].set_edgecolor(GOOD if done else AMBER)
            self.overlays[region].set_alpha(.45 if done else .9)
        released = state.release_step is not None
        self.overlays['l3'].set_hatch(None if released else '///')
        self.overlays['l3'].set_edgecolor(BAD if state.violation_step is not None else GOOD if released else AMBER)
        if state.violation_step is not None:
            text = f'UNTIL VIOLATED at step {state.violation_step}'
            color = BAD
        elif released:
            text, color = f'L3 RESTRICTION RELEASED  /  Type 2 reached L4 at step {state.release_step}', GOOD
        else:
            text, color = 'L3 RESTRICTED  /  At most one Type 1 robot until Type 2 reaches L4', AMBER
        self.banner.set_text(text)
        self.banner.set_color(color)
        self.team_ring.set_offsets(np.array([positions[r]+.5 for r in team]).reshape(-1, 2))
        self.cursor.set_xdata([step, step])
        for event, marker, label in self.event_artists:
            color = (BAD if event.kind == '!' else GOOD) if event.step <= step else '#506177'
            marker.set_color(color)
            label.set_color(color)
        self.view.status.set_text(f'{"PAUSED" if self.view.paused else "REPLAY"}  /  {state.state}  /  Logic checked at integer steps')
