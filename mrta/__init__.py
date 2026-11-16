"""Multi-robot task allocation.

Submodules load on demand so visualization and replay do not require Gurobi.
"""
from importlib import import_module

__all__ = ['workspace_case1', 'task', 'buchi_parse', 'poset', 'weighted_ts',
           'weighted_ts_suffix', 'milp', 'milp_suf', 'vis', 'GMAPP']


def __getattr__(name):
    if name in __all__:
        module = import_module(f'.{name}', __name__)
        globals()[name] = module
        return module
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
