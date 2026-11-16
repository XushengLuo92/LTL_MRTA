"""Regression checks for deterministic playback and the portable demo."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from mrta.demo import load_replay
from mrta.vis import Presentation, Trajectory, satisfied_ap, save_replay, vis

ROOT = Path(__file__).resolve().parent.parent


class PlaybackTests(unittest.TestCase):
    def test_first_frame_interpolation_and_terminal_hold(self):
        track = Trajectory({(7, 0): [(0, 0), (1, 0), (1, 1)]}, {(7, 0): [3, 3]})
        for step, expected in [(-1, [0, 0]), (0, [0, 0]), (.5, [.5, 0]), (2, [1, 1]), (20, [1, 1])]:
            np.testing.assert_allclose(track.position((7, 0), step), expected)
        self.assertEqual(track.horizon, 2)
        np.testing.assert_array_equal(track.position((7, 0), .5), track.position((7, 0), .5))

    def test_closed_suffix_wraps_without_jump(self):
        track = Trajectory({(1, 0): [(0, 0), (1, 0), (1, 1), (1, 0)]}, {(1, 0): [1, 3]})
        np.testing.assert_allclose(track.position((1, 0), 3), [1, 0])
        np.testing.assert_allclose(track.position((1, 0), 3.5), [1, .5])
        np.testing.assert_allclose(track.position((1, 0), 5), [1, 0])
        self.assertEqual(track.horizon, 5)
        with self.assertRaises(ValueError):
            Trajectory({(1, 0): [(0, 0), (1, 0)]}, {(1, 0): [0, 1]})

    def test_single_cell_path(self):
        track = Trajectory({(1, 0): [(2, 3)]}, {(1, 0): [1, 1]})
        np.testing.assert_allclose(track.position((1, 0), 0), [2, 3])
        self.assertEqual(track.horizon, 0)

    def test_multicell_conjunction_and_stale_conditions(self):
        workspace = SimpleNamespace(regions={'l1': [(0, 0), (1, 0)], 'l2': (2, 0)})
        ap = [[('l1', 1, 2), ('l2', 2, 1)]]
        positions = {(1, 0): (0, 0), (1, 1): (1, 0), (2, 0): (2, 0)}
        self.assertEqual(satisfied_ap(workspace, positions, ap), {('l1', 1): [1, 2], ('l2', 2): [1]})
        positions[(1, 0)] = (0, 1)
        self.assertEqual(satisfied_ap(workspace, positions, ap), {})

    def test_sample_motion_has_no_obstacle_vertex_or_edge_collisions(self):
        workspace, paths, times, _, _ = load_replay(ROOT / 'demo/sample.json')
        track = Trajectory(paths, times)
        obstacles = {tuple(p) for region in workspace.obstacles.values() for p in region}
        previous = None
        for step in range(track.horizon + 1):
            points = track.positions(step)
            unique = {tuple(p) for p in points.values()}
            self.assertEqual(len(unique), len(paths))
            self.assertFalse(unique & obstacles)
            if previous:
                for robot, point in points.items():
                    self.assertLessEqual(np.abs(point - previous[robot]).sum(), 1)
                    for other in points:
                        if other != robot:
                            self.assertFalse(np.array_equal(point, previous[other]) and
                                             np.array_equal(points[other], previous[robot]))
            previous = points

    def test_render_controls_and_replay_roundtrip(self):
        workspace, paths, times, ap, data = load_replay(ROOT / 'demo/sample.json')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'replay.json'
            save_replay(output, workspace, paths, times, ap, data['title'], data['subtitle'])
            loaded = load_replay(output)
            self.assertEqual(loaded[1], paths)
            view = Presentation(*loaded[:4])
            try:
                view.draw(5.5)
                first = view.groups[0][2].get_offsets().copy()
                view.draw(5.5)
                np.testing.assert_array_equal(first, view.groups[0][2].get_offsets())
                view.on_key(SimpleNamespace(key=' '))
                self.assertTrue(view.paused)
                view.on_key(SimpleNamespace(key='right'))
                self.assertEqual(view.step, 6.5)
                view.on_key(SimpleNamespace(key='r'))
                self.assertEqual(view.step, 0)
                view.save(Path(directory) / 'frame.png', dpi=40)
                self.assertGreater((Path(directory) / 'frame.png').stat().st_size, 1000)
            finally:
                plt.close(view.fig)

    def test_existing_vis_api_exports_poster_and_json(self):
        workspace, paths, times, ap, _ = load_replay(ROOT / 'demo/sample.json')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'nested' / 'case.png'
            vis(1, workspace, paths, times, ap, output=output)
            self.assertTrue(output.exists())
            self.assertEqual(len(load_replay(output.with_suffix('.json'))[1]), 5)


if __name__ == '__main__':
    unittest.main()
