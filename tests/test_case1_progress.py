"""Case 1 semantics and motion/UI synchronization, independent of Gurobi."""
from itertools import combinations
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from mrta.demo import load_replay
from mrta.ltl_progress import CASE1_FORMULA, Case1Monitor
from mrta.task import Task
from mrta.vis import Presentation, Trajectory, save_replay, vis

ROOT = Path(__file__).resolve().parent.parent
PAIR = ((1, 0), (1, 1))
WORKSPACE = SimpleNamespace(regions={'l2': [(0, 0), (0, 1)],
                                    'l3': [(1, 0), (1, 1)], 'l4': [(2, 0)]})


def monitor(rows, team=PAIR):
    # Each row: region of R1, R2, R3 (Type 1), and R1 (Type 2).
    locations = {'A': (0, 0), 'B': (1, 0), 'C': (2, 0), '-': (3, 0)}
    robots = [(1, 0), (1, 1), (1, 2), (2, 0)]
    paths = {r: [locations[row[i]] for row in rows] for i, r in enumerate(robots)}
    trajectory = Trajectory(paths, {r: [len(rows)]*2 for r in robots})
    mission = {'case': 1}
    if team is not None:
        mission['team'] = team
    return Case1Monitor(WORKSPACE, trajectory, mission)


class Case1Tests(unittest.TestCase):
    def test_monitor_specification_matches_planner_task(self):
        self.assertEqual(CASE1_FORMULA, Task(1).formula)

    def test_visit_memory_and_persistent_release(self):
        m = monitor(['AA--', '---C', '----', 'BB--', '----'])
        self.assertEqual(m.at(0).a_step, 0)
        self.assertEqual(m.at(1).l2, ())
        self.assertEqual(m.at(1).a_step, 0)
        self.assertEqual(m.at(2).l4, ())
        self.assertEqual(m.at(2).release_step, 1)
        self.assertTrue(m.at(3).satisfied)
        self.assertTrue(m.at(4).satisfied)
        self.assertEqual([e.kind for e in m.events], ['A', 'C', 'B'])

    def test_early_entry_is_irreversible_violation(self):
        m = monitor(['AA--', 'BB--', '---C', 'BB--'])
        self.assertEqual(m.at(1).violation_step, 1)
        self.assertEqual(m.at(3).release_step, 2)
        self.assertEqual(m.at(3).state, 'VIOLATED')
        self.assertFalse(m.at(3).satisfied)

    def test_release_and_arrival_on_same_step_are_valid(self):
        m = monitor(['AA--', 'BB-C'])
        self.assertTrue(m.at(1).satisfied)
        self.assertIsNone(m.at(1).violation_step)

    def test_one_type1_is_allowed_before_release(self):
        m = monitor(['AA--', 'B---', 'B--C', 'BB--'])
        self.assertIsNone(m.at(1).violation_step)
        self.assertTrue(m.at(3).satisfied)

    def test_restriction_counts_unassigned_type1_robots(self):
        m = monitor(['AA--', '-BB-', '---C'])
        self.assertEqual(m.at(1).violation_step, 1)

    def test_same_pair_and_order_are_required(self):
        self.assertFalse(monitor(['AA-C', 'B-B-']).at(1).satisfied)
        self.assertFalse(monitor(['BB-C', 'AA--']).at(1).satisfied)
        self.assertIsNone(monitor(['A--C', '-A--', 'BB--']).at(2).a_step)

    def test_missing_release_stays_pending(self):
        m = monitor(['AA--', '----'])
        self.assertEqual(m.at(1).state, 'IN PROGRESS')
        self.assertIsNone(m.at(1).release_step)

    def test_negative_condition_at_l2_applies_even_after_release(self):
        # Overlapping regions deliberately exercise A & !D independently of until.
        workspace = SimpleNamespace(regions={'l2': [(0, 0)], 'l3': [(0, 0)], 'l4': [(2, 0)]})
        paths = {(1, 0): [(0, 0)], (1, 1): [(0, 0)], (2, 0): [(2, 0)]}
        m = Case1Monitor(workspace, Trajectory(paths, {r: [1, 1] for r in paths}), {'case': 1, 'team': PAIR})
        self.assertEqual(m.at(0).release_step, 0)
        self.assertIsNone(m.at(0).a_step)
        self.assertFalse(m.at(0).satisfied)

    def test_unassigned_replay_tracks_all_candidate_pairs(self):
        m = monitor(['AA-C', '-AA-', '-BB-'], team=None)
        self.assertTrue(m.at(2).satisfied)
        self.assertEqual(m.at(2).team, ((1, 1), (1, 2)))
        self.assertEqual(m.at(2).a_step, 1)
        self.assertEqual([(e.kind, e.step) for e in m.events if e.kind == 'A'], [('A', 0), ('A', 1)])

    def test_rewind_has_no_future_information_or_fractional_events(self):
        m = monitor(['AA--', '---C', 'BB--'])
        self.assertTrue(m.at(2).satisfied)
        self.assertIsNone(m.at(.999).release_step)
        self.assertFalse(m.at(0).satisfied)
        self.assertEqual(len(m.at(0).events), 1)
        self.assertEqual(m.at(1), m.at(1))

    def test_monitor_matches_independent_bounded_formula_oracle(self):
        rng = random.Random(42)
        for _ in range(180):
            rows = [''.join(rng.choice('AB-') for _ in range(3)) + rng.choice('C-') for _ in range(6)]
            for team in (PAIR, None):
                c_steps = [t for t, row in enumerate(rows) if row[3] == 'C']
                until = bool(c_steps) and all(rows[t][:3].count('B') < 2 for t in range(c_steps[0]))
                pairs = [(0, 1)] if team else list(combinations(range(3), 2))
                ordered = any(all(rows[a][r] == 'A' for r in pair) and rows[a][:3].count('B') < 2
                              and all(rows[b][r] == 'B' for r in pair)
                              for pair in pairs for a in range(len(rows)) for b in range(a, len(rows)))
                self.assertEqual(monitor(rows, team).at(5).satisfied, until and ordered, rows)

    def test_invalid_assignment_and_formula_fail_explicitly(self):
        for team in [(), ((1, 0), (1, 0)), ((1, 0), (2, 0)), ((1, 0), (1, 9))]:
            with self.assertRaises(ValueError):
                monitor(['AA-C'], team)
        trajectory = Trajectory({(1, 0): [(0, 0)]}, {(1, 0): [1, 1]})
        with self.assertRaises(ValueError):
            Case1Monitor(WORKSPACE, trajectory, {'case': 1, 'formula': 'F A'})

    def test_demo_paths_are_valid_and_complete_case1(self):
        workspace, paths, times, _, data = load_replay(ROOT / 'demo/case1.json')
        trajectory = Trajectory(paths, times)
        m = Case1Monitor(workspace, trajectory, data['mission'])
        self.assertEqual([(e.kind, e.step) for e in m.events], [('A', 1), ('C', 10), ('B', 20)])
        self.assertTrue(m.at(trajectory.horizon).satisfied)
        obstacles = {tuple(p) for cells in workspace.obstacles.values() for p in cells}
        previous = None
        for step in range(trajectory.horizon + 1):
            points = trajectory.positions(step)
            unique = {tuple(p) for p in points.values()}
            self.assertEqual(len(unique), len(paths))
            self.assertFalse(unique & obstacles)
            for robot, point in points.items():
                self.assertTrue(0 <= point[0] < workspace.width and 0 <= point[1] < workspace.length)
                if previous:
                    self.assertLessEqual(np.abs(point-previous[robot]).sum(), 1)
                    for other in points:
                        if other != robot:
                            self.assertFalse(np.array_equal(point, previous[other]) and
                                             np.array_equal(points[other], previous[robot]))
            previous = points

    def test_mission_roundtrip_and_linked_ui_navigation(self):
        workspace, paths, times, ap, data = load_replay(ROOT / 'demo/case1.json')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'mission.json'
            save_replay(output, workspace, paths, times, ap, data['title'], data['subtitle'], data['mission'])
            loaded = load_replay(output)
            self.assertEqual(loaded[4]['mission'], data['mission'])
            view = Presentation(*loaded[:4], mission=loaded[4]['mission'])
            try:
                panel = view.mission_view
                view.draw(9.99)
                self.assertEqual(panel.overlays['l3'].get_hatch(), '///')
                view.draw(10)
                self.assertIsNone(panel.overlays['l3'].get_hatch())
                self.assertIn('RELEASED', panel.banner.get_text())
                view.draw(14)
                self.assertIn('RELEASED', panel.banner.get_text())
                view.on_key(SimpleNamespace(key='p'))
                self.assertEqual(view.step, 10)
                view.on_key(SimpleNamespace(key='n'))
                self.assertEqual(view.step, 20)
                self.assertIn('SATISFIED', panel.verdict.get_text())
                panel.seek(SimpleNamespace(inaxes=panel.timeline, xdata=8))
                self.assertEqual(view.step, 8)
                self.assertEqual(panel.overlays['l3'].get_hatch(), '///')
                view.on_key(SimpleNamespace(key='r'))
                self.assertEqual(view.step, 0)
                view.save(Path(directory) / 'mission.png', dpi=40)
            finally:
                plt.close(view.fig)
            vis(1, workspace, paths, times, ap, mission=data['mission'], output=Path(directory)/'planner.png')
            self.assertEqual(load_replay(Path(directory)/'planner.json')[4]['mission'], data['mission'])


if __name__ == '__main__':
    unittest.main()
