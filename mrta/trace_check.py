"""Evaluate the repository's LTL syntax on a finite prefix plus repeating cycle.

The future operators use least/greatest fixed points on the lasso, not a finite
animation's last frame. Robot-binding IDs are evaluated using planner assignments.
"""
from functools import lru_cache
from itertools import combinations, product
import re

import numpy as np


class FormulaParser:
    def __init__(self, formula):
        token = r'\[\]|<>|&&|\|\||->|[!()]|[A-Za-z][A-Za-z0-9_]*'
        self.tokens = re.findall(token, formula)
        if ''.join(self.tokens) != re.sub(r'\s+', '', formula):
            raise ValueError('Unsupported LTL token.')
        self.index = 0

    def peek(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def take(self):
        value = self.peek()
        self.index += 1
        return value

    def parse(self):
        node = self.expression(0)
        if self.peek() is not None:
            raise ValueError(f'Unexpected token {self.peek()}')
        return node

    def expression(self, minimum):
        value = self.take()
        if value in ('!', '[]', '<>', 'X'):
            left = (value, self.expression(5))
        elif value == '(':
            left = self.expression(0)
            if self.take() != ')':
                raise ValueError('Missing closing parenthesis.')
        elif value is not None and re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', value) and value != 'U':
            left = ('atom', value)
        else:
            raise ValueError(f'Unexpected token {value}')
        # Match ltl2ba/parse.c: Boolean binary operators share a level,
        # until binds more tightly, and both levels associate to the left.
        priorities = {'->': 1, '||': 1, '&&': 1, 'U': 2}
        while self.peek() in priorities and priorities[self.peek()] >= minimum:
            operator = self.take()
            priority = priorities[operator]
            right = self.expression(priority + 1)
            left = (operator, left, right)
        return left


def evaluate_lasso(formula, valuations, loop_start):
    """Return whether formula holds at time zero on an infinite lasso trace."""
    length = len(valuations)
    if not length or not 0 <= loop_start < length:
        raise ValueError('Invalid lasso.')
    successors = np.array(list(range(1, length)) + [loop_start])
    tree = FormulaParser(formula).parse()

    @lru_cache(None)
    def evaluate(node):
        op = node[0]
        if op == 'atom':
            if node[1] in ('true', 'false'):
                return np.full(length, node[1] == 'true')
            return np.array([row[node[1]] for row in valuations], dtype=bool)
        a = evaluate(node[1])
        if op == '!': return ~a
        if op == 'X': return a[successors]
        if op in ('<>', '[]', 'U'):
            value = np.ones(length, dtype=bool) if op == '[]' else np.zeros(length, dtype=bool)
            b = evaluate(node[2]) if op == 'U' else None
            while True:
                new = a & value[successors] if op == '[]' else a | value[successors] if op == '<>' else b | (a & value[successors])
                if np.array_equal(value, new): return new
                value = new
        b = evaluate(node[2])
        if op == '&&': return a & b
        if op == '||': return a | b
        if op == '->': return ~a | b
        raise ValueError(f'Unsupported operator {op}')
    return bool(evaluate(tree)[0])


def region_members(workspace, positions, region, kind):
    cells = {tuple(cell) for cell in np.asarray(workspace.regions[region]).reshape(-1, 2)}
    return tuple(sorted(r for r, p in positions.items() if r[0] == kind and tuple(p) in cells))


def proposition(workspace, positions, name, bindings):
    region, kind, number, *identity = name.split('_')
    kind, number = int(kind), int(number)
    members = region_members(workspace, positions, region, kind)
    if identity and identity[0] != '0':
        selected = bindings.get(identity[0])
        if selected is None:
            raise ValueError(f'Missing robot binding {identity[0]} for {name}')
        members = [r for r in members if r[1] in selected]
    return len(members) >= number


def validate_replay(workspace, trajectory, mission):
    violations = []
    obstacles = {tuple(c) for group in workspace.obstacles.values() for c in np.asarray(group).reshape(-1, 2)}
    previous = None
    for step in range(trajectory.horizon + 1):
        positions = trajectory.positions(step)
        for robot, p in positions.items():
            if tuple(p) in obstacles or not (0 <= p[0] < workspace.width and 0 <= p[1] < workspace.length):
                violations.append({'step': step, 'robot': robot, 'reason': 'invalid cell'})
            if previous is not None and np.abs(p - previous[robot]).sum() > 1:
                violations.append({'step': step, 'robot': robot, 'reason': 'non-grid move'})
        for a, b in combinations(positions, 2):
            if np.array_equal(positions[a], positions[b]):
                violations.append({'step': step, 'robots': [a, b], 'reason': 'vertex collision'})
            elif previous is not None and np.array_equal(positions[a], previous[b]) and np.array_equal(positions[b], previous[a]):
                violations.append({'step': step, 'robots': [a, b], 'reason': 'edge collision'})
        previous = positions
    horizon = trajectory.horizon
    start, end = mission.get('loop_start', horizon), mission.get('loop_end', horizon)
    if not 0 <= start <= end <= horizon:
        raise ValueError('Loop boundaries are outside the replay.')
    loop_closed = all(np.array_equal(trajectory.position(r, start), trajectory.position(r, end)) for r in trajectory.paths)
    if not loop_closed:
        raise ValueError('Suffix is not a closed cycle.')
    length = end if end > start else end + 1
    atoms = set(re.findall(r'[lp]\d+_\d+_\d+(?:_\d+)?', mission['formula']))
    bindings = mission.get('bindings', {})
    if not bindings and mission.get('team'):
        bindings = {'1': [r[1] for r in mission['team']]}
    # An implication can be vacuous, leaving its binding unassigned by the MILP.
    # Search an explicit witness for those IDs; never invent a planner assignment.
    missing = {}
    for atom in sorted(atoms):
        _, kind, count, *identity = atom.split('_')
        if identity and identity[0] != '0' and identity[0] not in bindings:
            spec = (int(kind), int(count))
            if identity[0] in missing and missing[identity[0]] != spec:
                raise ValueError('An unbound identity has inconsistent type/count requirements.')
            missing[identity[0]] = spec
    choices = [list(combinations([r[1] for r in trajectory.paths if r[0] == kind], count))
               for kind, count in missing.values()]
    satisfied, witness = False, dict(bindings)
    for selection in product(*choices):
        witness = {**bindings, **dict(zip(missing, selection))}
        valuations = [{atom: proposition(workspace, trajectory.positions(t), atom, witness) for atom in atoms}
                      for t in range(length)]
        if evaluate_lasso(mission['formula'], valuations, start):
            satisfied = True
            break
    return {'motion_valid': not violations, 'violations': violations, 'ltl_satisfied_on_repeating_cycle': satisfied,
            'loop_start': start, 'loop_end': end, 'loop_closed': loop_closed, 'horizon': horizon,
            'robot_count': len(trajectory.paths), 'witness_bindings': witness,
            'bindings_inferred_for_validation_only': list(missing)}
