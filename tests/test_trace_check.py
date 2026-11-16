"""Temporal semantics, binding preservation, and recurring replay controls."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from mrta.demo import load_replay
from mrta.replay_export import export_plan
from mrta.run_panel import RunMonitor
from mrta.task import Task
from mrta.trace_check import FormulaParser, evaluate_lasso, validate_replay
from mrta.vis import Presentation, Trajectory


def fixture():
    workspace = SimpleNamespace(width=5, length=3, regions={'l2': [(0,0)], 'l3': [(1,0)], 'r1': [(0,0)]}, obstacles={})
    paths = {(1,0): [(0,0),(1,0),(0,0),(1,0),(0,0)], (1,1): [(3,0)]*5}
    times = {r: [5,5] for r in paths}
    stages = []
    for step,region,phase in [(0,'l2','Prefix'),(1,'l3','Cycle 1'),(2,'r1','Cycle 1'),(3,'l3','Cycle 2'),(4,'r1','Cycle 2')]:
        stages.append(dict(step=step,phase=phase,positive=[] if region=='r1' else [[region,1,1,1]],
                           negative=[],assigned={region:[[1,0]]},holding={},avoid=[]))
    mission = dict(case=2,formula=Task(2).formula,bindings={'1':[0]},loop_start=0,loop_end=2,stages=stages)
    return workspace,paths,times,mission


class TraceTests(unittest.TestCase):
    def test_recurrence_requires_witness_in_cycle(self):
        rows=[{'p':True},{'p':False}]
        self.assertTrue(evaluate_lasso('<> p',rows,1))
        self.assertFalse(evaluate_lasso('[] <> p',rows,1))
        self.assertTrue(evaluate_lasso('[] <> p',rows,0))
        self.assertFalse(evaluate_lasso('[] p',rows,0))

    def test_strong_until_and_same_step_release(self):
        self.assertTrue(evaluate_lasso('!p U q',[{'p':True,'q':True}],0))
        self.assertFalse(evaluate_lasso('!p U q',[{'p':False,'q':False}],0))
        self.assertFalse(evaluate_lasso('!p U q',[{'p':True,'q':False},{'p':False,'q':True}],1))

    def test_next_holding_obligation(self):
        formula='[] (p -> X (p U q))'
        self.assertTrue(evaluate_lasso(formula,[{'p':True,'q':False},{'p':False,'q':True}],1))
        self.assertFalse(evaluate_lasso(formula,[{'p':True,'q':True},{'p':False,'q':False}],1))
        self.assertFalse(evaluate_lasso(formula,[{'p':True,'q':False},{'p':False,'q':False},{'p':False,'q':True}],2))

    def test_global_disjunction_cannot_alternate_between_global_claims(self):
        rows=[{'p':True,'q':False},{'p':False,'q':True}]
        self.assertTrue(evaluate_lasso('[] (p || q)',rows,0))
        self.assertFalse(evaluate_lasso('[] p || [] q',rows,0))
        self.assertTrue(evaluate_lasso('[]<>p && []<>q',rows,0))

    def test_parser_accepts_every_repository_formula_and_rejects_bad_input(self):
        for case in range(1,11):
            self.assertIsNotNone(FormulaParser(Task(case,4).formula).parse())
        for value in ['<> p $ q', '(p', 'p &&', '', 'p q']:
            with self.assertRaises(ValueError): FormulaParser(value).parse()

    def test_precedence_and_associativity_match_ltl2ba(self):
        self.assertFalse(evaluate_lasso('a || b && c', [{'a':True,'b':False,'c':False}], 0))
        rows=[{'p':True,'q':False,'r':False},{'p':False,'q':False,'r':True}]
        self.assertFalse(evaluate_lasso('p U q U r', rows, 1))
        self.assertTrue(evaluate_lasso('p U (q U r)', rows, 1))

    def test_cycle_closure_and_actual_assigned_robot(self):
        w,p,t,m=fixture()
        report=validate_replay(w,Trajectory(p,t),m)
        self.assertTrue(report['motion_valid'])
        self.assertTrue(report['ltl_satisfied_on_repeating_cycle'])
        m['bindings']={'1':[1]}
        self.assertFalse(validate_replay(w,Trajectory(p,t),m)['ltl_satisfied_on_repeating_cycle'])
        m['loop_end']=1
        with self.assertRaises(ValueError): validate_replay(w,Trajectory(p,t),m)

    def test_unassigned_binding_is_an_explicit_validation_witness(self):
        w,p,t,m=fixture();m['bindings']={}
        report=validate_replay(w,Trajectory(p,t),m)
        self.assertTrue(report['ltl_satisfied_on_repeating_cycle'])
        self.assertEqual(report['bindings_inferred_for_validation_only'],['1'])
        self.assertEqual(report['witness_bindings']['1'],(0,))
        self.assertEqual(m['bindings'],{})

    def test_stage_uses_robot_identity_and_seek_restores_progress(self):
        w,p,t,m=fixture()
        monitor=RunMonitor(w,Trajectory(p,t),m)
        self.assertTrue(all(monitor.valid))
        m['stages'][1]['assigned']={'l3':[[1,1]]}
        monitor=RunMonitor(w,Trajectory(p,t),m)
        self.assertFalse(monitor.valid[1])
        m['stages'][1]['assigned']={'l3':[[1,0]]}
        view=Presentation(w,p,t,mission=m)
        try:
            view.draw(4)
            self.assertEqual(len(view.mission_view.monitor.state(4)[0]),5)
            view.mission_view.seek(SimpleNamespace(inaxes=view.mission_view.timeline,xdata=0))
            self.assertEqual(view.step,0)
            self.assertEqual(len(view.mission_view.monitor.state(0)[0]),1)
            view.on_key(SimpleNamespace(key='n'))
            self.assertEqual(view.step,1)
            with tempfile.TemporaryDirectory() as folder:
                view.save(Path(folder)/'frame.png',dpi=40)
        finally: plt.close(view.fig)

    def test_export_keeps_prefix_and_suffix_assignments(self):
        w,p,t,m=fixture()
        def stage(step,region):
            return dict(subtask=('q0','q1'),time_element=[step,0],essential_clause_edge=[[region,1,1,1]],
                        neg_edge=[],essential_robot_vertex={},neg_vertex=[],essential_robot_edge={region:[(1,0)]})
        with tempfile.TemporaryDirectory() as folder:
            args=SimpleNamespace(case=2,output_dir=folder,replay_only=True)
            export_plan(args,w,p,Task(2),{1:[0]},[stage(0,'l2')],prefix_paths={r: v[:1] for r,v in p.items()},
                        suffix_paths={r: v[:3] for r,v in p.items()},suffix_run=[stage(1,'l3')],suffix_bindings={1:[0]})
            data=load_replay(Path(folder)/'case_02.json')[4]
            self.assertEqual(data['mission']['loop_end'],2)
            self.assertEqual([s['step'] for s in data['mission']['stages']],[0,1,3])
            with self.assertRaises(ValueError):
                export_plan(args,w,p,Task(2),{1:[0]},[stage(0,'l2')],suffix_bindings={1:[1]})


if __name__ == '__main__': unittest.main()
