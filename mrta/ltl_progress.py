"""Position-based monitor for the exact Case 1 task, not a general LTL engine.

F((A & !D) & F B) & F C & (!D U C)
A/B: the same Type 1 pair together in L2/L3; C: any Type 2 in L4;
D: any two Type 1 robots in L3. Positive witnesses persist; APs do not.
"""
from dataclasses import dataclass
from itertools import combinations
import math

import numpy as np

CASE1_FORMULA = '<> ((l2_1_2_1 && ! l3_1_2) && <> l3_1_2_1) && <> l4_2_1_0 && (! l3_1_2 U l4_2_1_0)'


@dataclass(frozen=True)
class Event:
    step: int
    kind: str
    text: str


@dataclass(frozen=True)
class Snapshot:
    step: int
    l2: tuple
    l3: tuple
    l4: tuple
    team: tuple
    a_step: int | None
    b_step: int | None
    release_step: int | None
    violation_step: int | None
    events: tuple

    @property
    def satisfied(self):
        return self.b_step is not None and self.release_step is not None and self.violation_step is None

    @property
    def state(self):
        return 'VIOLATED' if self.violation_step is not None else ('SATISFIED' if self.satisfied else 'IN PROGRESS')


class Case1Monitor:
    def __init__(self, workspace, trajectory, mission):
        if mission.get('case') != 1:
            raise ValueError('Only the Case 1 mission monitor is supported.')
        if mission.get('formula', CASE1_FORMULA) != CASE1_FORMULA:
            raise ValueError('Case 1 mission formula does not match the supported specification.')
        for region in ('l2', 'l3', 'l4'):
            if region not in workspace.regions:
                raise ValueError(f'Case 1 requires region {region}.')
        self.assignment = tuple(sorted(tuple(r) for r in mission.get('team', [])))
        if 'team' in mission and (len(set(self.assignment)) != 2 or len(self.assignment) != 2 or
                                any(r not in trajectory.paths or r[0] != 1 for r in self.assignment)):
            raise ValueError('The Case 1 team must contain two distinct Type 1 robots in the replay.')
        self.snapshots = []
        candidates = {}  # Every eligible pair, not just a greedy first match.
        release = violation = completed = None
        chosen = ()
        events = []
        for step in range(math.floor(trajectory.horizon) + 1):
            positions = trajectory.positions(step)
            def members(region, kind):
                region_cells = np.asarray(workspace.regions[region], dtype=float).reshape(-1, 2)
                return tuple(sorted(r for r, p in positions.items() if r[0] == kind and
                                    np.any(np.all(np.isclose(region_cells, p, atol=1e-8, rtol=0), axis=1))))
            l2, l3, l4 = members('l2', 1), members('l3', 1), members('l4', 2)
            # Strong until permits D on the very same step C first becomes true.
            if release is None:
                if l4:
                    release = step
                    events.append(Event(step, 'C', f'Type 2 / R{l4[0][1]+1} reaches L4. Restriction released.'))
                elif len(l3) >= 2 and violation is None:
                    violation = step
                    events.append(Event(step, '!', 'Two Type 1 robots entered L3 before release.'))
            if len(l3) < 2 and completed is None:
                eligible = [self.assignment] if self.assignment else list(combinations(l2, 2))
                new_pairs = []
                for pair in eligible:
                    if set(pair).issubset(l2) and pair not in candidates:
                        candidates[pair] = step
                        new_pairs.append(' + '.join(f'R{r[1]+1}' for r in pair))
                if new_pairs:
                    events.append(Event(step, 'A', f'Type 1 {", ".join(new_pairs)} visits L2 with fewer than two Type 1 in L3.'))
            if completed is None:
                for pair, first_step in candidates.items():
                    if set(pair).issubset(l3):
                        completed, chosen = step, pair
                        events.append(Event(step, 'B', 'The same Type 1 pair reaches L3. Ordered visits witnessed.'))
                        break
            team = chosen or self.assignment or next(iter(candidates), ())
            self.snapshots.append(Snapshot(step, l2, l3, l4, team, candidates.get(team),
                                           completed, release, violation, tuple(events)))
        self.events = tuple(events)

    def at(self, step):
        # Integer states are the only semantic ticks; interpolation is visual only.
        return self.snapshots[min(max(0, math.floor(step + 1e-9)), len(self.snapshots) - 1)]
