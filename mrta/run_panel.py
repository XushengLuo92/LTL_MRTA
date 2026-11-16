"""Selected-run progress for recurring Cases 2–10, linked to real positions."""
import math
import textwrap

import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import FancyBboxPatch, Rectangle

from .ltl_progress import Event
from .trace_check import FormulaParser, region_members, validate_replay
from .vis import BG, PANEL, INK, MUTED, COLORS, cells

GOOD, AMBER, BAD = COLORS[0], COLORS[1], '#ff829c'


def specification(case, n):
    return {
        2: ('G F(A ∧ F B)', ['A: Type 1 at L2; B: the same robot at L3.']),
        3: ('G F(A ∧ F(B ∧ F(C ∧ F D)))', ['A / B / C / D: the same two Type 1 robots', 'visit L2 / L3 / L4 / L5, respectively.']),
        4: ('G F(A ∧ F B) ∧ G(C → X(C U D)) ∧ G ¬E', ['A / B: same Type 1 pair at L2 / L3.', 'C: selected Type 1 at L5; D: Type 2 at L4.', 'E: two Type 1 at L4.']),
        5: ('F(A ∧ X(A U B)) ∧ G F(A ∧ F C)', ['A / C: same Type 2 robot at L4 / L3.', 'B: two Type 1 robots at L3.']),
        6: ('G F(A ∨ B) ∧ G F(C ∨ D) ∧ G F E\n∧ G ¬P ∧ G ¬Q', ['A / B: same Type 1 at L3 / L5; E: that robot at L2.', 'C / D: two Type 2 at L3 / L5.', 'P / Q: two Type 1 / Type 2 at L4.']),
        7: ('G F(A ∧ X F ¬A) ∧ G F(B ∧ X F ¬B) ∧ F C', ['A: Type 2 at L4; B: Type 1 at L5.', 'C: three Type 1 and two Type 2 together at L3.']),
        8: ('G F(A ∧ F(B ∧ F C)) ∧ (¬P U A)\n∧ (¬Q U A) ∧ (G F D ∨ G F E)', ['A / B / C: same Type 2 pair at L4 / L2 / L5.', 'P / Q: any Type 2 at L2 / L5.', 'D / E: two Type 1 at L5 / L3.']),
        9: ('G F A ∧ G F B ∧ G F C ∧ (¬D U (E ∧ H))', [f'A: {n} Type 1 at L2; B / C: {n//2} at L3 / L4.', 'D: any Type 1 at L4.', 'E / H: Type 1 at L5 / L6.']),
        10: ('G F A ∧ G F(B ∧ F C) ∧ F(D ∨ E) ∧ G ¬H', [f'A: {n//4} Type 1 at L3; B / C: same {n//2} at L2 / L4.', 'D / E: three Type 1 at L5 / L6.', 'H: four Type 1 at L6.']),
    }[case]


def target_text(stage):
    if stage['positive']:
        return '; '.join(f'{lit[0].upper()}: {lit[2]} Type {lit[1]}' for lit in stage['positive'])
    if stage['assigned']:
        return 'Return robots to the cycle-start positions'
    return 'Advance the selected automaton transition'


class RunMonitor:
    def __init__(self, workspace, trajectory, mission):
        self.workspace, self.trajectory, self.mission = workspace, trajectory, mission
        self.stages = [s for s in mission['stages'] if s['positive'] or s['assigned']]
        self.events = tuple(Event(s['step'], str(i+1), target_text(s)) for i, s in enumerate(self.stages))
        self.valid = []
        for stage in self.stages:
            positions = trajectory.positions(stage['step'])
            assigned = all(tuple(r) in region_members(workspace, positions, region, r[0])
                           for region, robots in stage['assigned'].items() for r in robots)
            positive = all(len(region_members(workspace, positions, lit[0], lit[1])) >= lit[2]
                           for lit in stage['positive'])
            negative = all(len(region_members(workspace, positions, lit[0], lit[1])) < lit[2]
                           for lit in stage['negative'])
            self.valid.append(assigned and positive and negative)
        self.validation = validate_replay(workspace, trajectory, mission)
        self.always_avoid = []
        def collect(node):
            if node[0] == '&&':
                collect(node[1]); collect(node[2])
            elif node[0] == '[]' and node[1][0] == '!' and node[1][1][0] == 'atom':
                region, kind, count, *_ = node[1][1][1].split('_')
                self.always_avoid.append([region, int(kind), int(count)])
        collect(FormulaParser(mission['formula']).parse())

    def state(self, step):
        tick = math.floor(step + 1e-9)
        reached = [i for i, s in enumerate(self.stages) if s['step'] <= tick]
        future = next((i for i, s in enumerate(self.stages) if s['step'] > tick), None)
        current = next((i for i in reversed(reached) if self.stages[i]['step'] == tick), future)
        if current is None and self.stages:
            current = len(self.stages) - 1
        return reached, current, future


class RunPanel:
    def __init__(self, view, monitor):
        self.view, self.monitor = view, monitor
        self.mission = monitor.mission
        view.panel.set_visible(False)
        view.ax.set_position([.045, .19, .475, .72])
        view.ax.tick_params(labelbottom=False)
        view.progress.axes.set_position([.055, .04, .9, .006])
        self.ax = view.fig.add_axes([.565, .19, .39, .72], facecolor=PANEL)
        self.ax.set(xlim=(0, 1), ylim=(0, 1), xticks=[], yticks=[])
        for spine in self.ax.spines.values(): spine.set_visible(False)
        self.text(.04, .955, f'CASE {self.mission["case"]} / LTL MISSION', 11, MUTED)
        self.clock = self.text(.96, .955, '', 10, MUTED, ha='right')
        formula, legend = specification(self.mission['case'], len(view.trajectory.paths))
        self.text(.04, .885, formula, 12, va='top', linespacing=1.4)
        for i, line in enumerate(legend):
            self.text(.04, .785 - i*.042, line, 9, MUTED)
        self.cards = []
        for y, heading in [(.46, 'TASK EVENT'), (.24, 'ACTIVE RESTRICTIONS'), (.02, 'RECURRENT EXECUTION')]:
            card = FancyBboxPatch((.035, y), .93, .19, boxstyle='round,pad=0.008,rounding_size=0.012',
                                  facecolor=BG, edgecolor='#294057', linewidth=1.1)
            self.ax.add_patch(card)
            self.text(.065, y+.145, heading, 11)
            badge = self.text(.935, y+.145, '', 9, ha='right')
            body = self.text(.065, y+.096, '', 10, MUTED, va='top', linespacing=1.6)
            self.cards.append((card, badge, body))
        self.overlays = {}
        for region, values in view.workspace.regions.items():
            if region.startswith('r'): continue
            overlay = PatchCollection([Rectangle((x+.02,y+.02),.96,.96) for x,y in cells(values)],
                                      facecolors='none', edgecolors=AMBER, linewidths=1.3, zorder=2)
            view.ax.add_collection(overlay)
            self.overlays[region] = overlay
        self.team_ring = view.ax.scatter([], [], s=270 if view.workspace.width <= 10 else 140,
                                         facecolors='none', edgecolors=INK, linewidths=1.2, zorder=8)
        self.banner = view.fig.text(.055, .145, '', color=AMBER, fontsize=11, weight='bold')
        for i, kind in enumerate(sorted(view.type_colors)):
            view.fig.text(.055+i*.085, .94, f'{"●" if i == 0 else "■"}  TYPE {kind}',
                          color=view.type_colors[kind], fontsize=9)
        self.timeline = view.fig.add_axes([.075, .075, .86, .045], facecolor=BG)
        self.timeline.set(xlim=(-1, view.trajectory.horizon+1), ylim=(0,1))
        self.timeline.axis('off')
        self.timeline.plot([0,view.trajectory.horizon],[.45,.45],color='#294057',lw=2)
        self.cursor = self.timeline.axvline(0,color=INK,lw=1,alpha=.65)
        self.event_artists = []
        for i,event in enumerate(monitor.events):
            dot, = self.timeline.plot([event.step],[.45],marker='o',ms=6,color=MUTED)
            label = self.timeline.text(event.step,.85 if i%2==0 else .02,
                                       f'{event.step}',fontsize=8,color=MUTED,ha='center',va='center')
            self.event_artists.append((event,dot,label))
        view.fig.canvas.mpl_connect('button_press_event', self.seek)

    def text(self,x,y,value,size=10,color=INK,**kwargs):
        kwargs.setdefault('va','center')
        return self.ax.text(x,y,value,fontsize=size,color=color,**kwargs)

    def seek(self,event):
        if event.inaxes is self.timeline and event.xdata is not None:
            self.view.paused=True
            self.view.draw(round(event.xdata))
            self.view.fig.canvas.draw_idle()

    def draw(self,step,positions):
        reached,current,future = self.monitor.state(step)
        self.clock.set_text(f'STEP {step:05.1f} / {self.view.trajectory.horizon}')
        stage = self.monitor.stages[current] if current is not None else None
        active = self.monitor.stages[future] if future is not None else None
        if active is None:
            active = next((s for s in self.monitor.stages if s['phase'] == 'Cycle 1'), None)
        observed = current in reached
        color = GOOD if observed else AMBER
        if observed and not self.monitor.valid[current]: color=BAD
        card,badge,body = self.cards[0]
        card.set_edgecolor(color); badge.set_color(color)
        badge.set_text(('WITNESSED' if self.monitor.valid[current] else 'NOT OBSERVED') if observed else 'NEXT')
        goal = target_text(stage) if stage else 'No remaining task events'
        robots = sorted({tuple(r) for group in stage['assigned'].values() for r in group}) if stage else []
        robot_text = ' / '.join(f'Type {kind}: '+', '.join(f'R{r[1]+1}' for r in robots if r[0]==kind)
                                for kind in sorted({r[0] for r in robots}))
        if stage and len(robot_text)>65: robot_text=f'{len(robots)} assigned robots · {stage["phase"]}'
        body.set_text('\n'.join(textwrap.wrap(goal, 61)[:2]) + ('\n'+robot_text if robot_text else ''))
        self.team_ring.set_offsets(np.array([positions[r]+.5 for r in robots]).reshape(-1,2))
        restrictions = []
        forbidden = set()
        avoid = (active['avoid'] if active else []) + self.monitor.always_avoid
        for region,kind,count in dict.fromkeys(tuple(lit[:3]) for lit in avoid):
            restrictions.append(f'{region.upper()}: at most {count-1} Type {kind}')
            forbidden.add(region)
        if active:
            for region,team in active['holding'].items():
                if team:
                    restrictions.append(f'Keep {len(team)} assigned robot(s) at {region.upper()}')
        card,badge,body = self.cards[1]
        card.set_edgecolor(AMBER if restrictions else '#294057')
        badge.set_text('ENFORCED' if restrictions else 'NONE');badge.set_color(AMBER if restrictions else MUTED)
        body.set_text('\n'.join(restrictions[:3]) if restrictions else 'No additional holding / avoidance condition\nbefore the next selected task event.')
        for region,overlay in self.overlays.items():
            target = bool(stage and region in stage['assigned'])
            overlay.set_visible(target or region in forbidden)
            overlay.set_edgecolor(AMBER if region in forbidden else color)
            overlay.set_hatch('///' if region in forbidden else None)
        card,badge,body = self.cards[2]
        phase = stage['phase'] if stage else 'Prefix'
        start,end = self.mission.get('loop_start',0),self.mission.get('loop_end',0)
        if step < start: phase='Prefix'
        elif end>start: phase='Cycle 1' if step<end else 'Cycle 2'
        count = sum(self.monitor.valid[i] for i in reached)
        badge.set_text(phase.upper());badge.set_color(GOOD)
        body.set_text(f'{count} / {len(self.monitor.stages)} recorded task events witnessed\n'
                      + (f'Repeat the closed cycle from step {start} to {end}.' if end>start else 'The final accepting state is held.'))
        if not self.monitor.validation['ltl_satisfied_on_repeating_cycle'] or not self.monitor.validation['motion_valid']:
            card.set_edgecolor(BAD);badge.set_text('CHECK FAILED');badge.set_color(BAD)
        self.banner.set_text(('WITNESSED  /  ' if observed else 'NEXT  /  ') + goal)
        self.banner.set_color(color)
        self.cursor.set_xdata([step,step])
        for i,(event,dot,label) in enumerate(self.event_artists):
            tint = (GOOD if self.monitor.valid[i] else BAD) if event.step<=step else '#506177'
            dot.set_color(tint);label.set_color(tint)
