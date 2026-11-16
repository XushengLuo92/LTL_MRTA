"""Export actual planner trajectories with their selected accepting-run stages."""
from pathlib import Path

from .vis import save_replay, vis


def export_plan(args, workspace, paths, task, bindings, prefix_run, *, prefix_paths=None,
                suffix_paths=None, suffix_run=None, suffix_bindings=None):
    mission = {'case': args.case, 'formula': task.formula,
               'bindings': {str(k): [int(r) for r in robots] for k, robots in bindings.items()}}
    for key, robots in (suffix_bindings or {}).items():
        selected = [int(r) for r in robots]
        if str(key) in mission['bindings'] and set(selected) != set(mission['bindings'][str(key)]):
            raise ValueError(f'Robot binding {key} changes between prefix and suffix.')
        mission['bindings'][str(key)] = selected
    if args.case == 1:
        mission['team'] = [[1, int(r)] for r in bindings[1]]
    stages = []
    def append_stages(run, offset, phase):
        for stage in run:
            positive = stage['essential_clause_edge']
            stages.append({
                'step': int(stage['time_element'][0]) + offset,
                'phase': phase,
                'transition': list(stage['subtask']),
                'positive': [] if positive == '1' else [list(lit) for lit in positive],
                'negative': [list(lit) for lit in stage['neg_edge']],
                'holding': {region: [list(r) for r in robots]
                            for region, robots in stage['essential_robot_vertex'].items()},
                'avoid': [list(lit) for lit in stage['neg_vertex']],
                'assigned': {region: [list(r) for r in robots]
                             for region, robots in stage['essential_robot_edge'].items()},
            })
    append_stages(prefix_run, 0, 'Prefix')
    if suffix_paths is not None:
        start = len(next(iter(prefix_paths.values()))) - 1
        duration = len(next(iter(suffix_paths.values()))) - 1
        mission['loop_start'], mission['loop_end'] = start, start + duration
        append_stages(suffix_run, start, 'Cycle 1')
        append_stages(suffix_run, start + duration, 'Cycle 2')
    else:
        mission['loop_start'] = max(len(p) for p in paths.values()) - 1
        mission['loop_end'] = mission['loop_start']
    mission['stages'] = stages
    # Cast numpy scalar fields before serialization, keeping explicit robot identities.
    import json
    mission = json.loads(json.dumps(mission, default=lambda value: value.item()))
    stem = f'mapp_case{args.case}' if Path(args.output_dir) == Path('data') else f'case_{args.case:02d}'
    output = Path(args.output_dir) / f'{stem}.mp4'
    times = {r: [len(p)] * 2 for r, p in paths.items()}
    if args.replay_only:
        save_replay(output.with_suffix('.json'), workspace, paths, times, [],
                    f'Multi-robot coordination / Case {args.case}',
                    'LTL task allocation / planner trajectory playback', mission)
    else:
        vis(args.case, workspace, paths, times, [], output=output, mission=mission)
