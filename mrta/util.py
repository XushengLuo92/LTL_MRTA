import argparse
from termcolor import cprint

def create_parser():
    """ create parser

    Returns:
        _type_: _description_
    """
    parser = argparse.ArgumentParser(description='LTL_MRTA')
    parser.add_argument('--case', default=0, type=int)
    parser.add_argument('--robot', default=1, type=int)
    parser.add_argument('--print', action='store_true', help='Enable print to terminal')
    parser.add_argument('--vis', action='store_true', help='Enable visualization')
    parser.add_argument('--only_first', action='store_true', help='Stop upon find the first solution')
    parser.add_argument('--loop', action='store_true', help='Return to initial locations directly to close the suffix loop')
    parser.add_argument('--partial_or_full', default='f', type=str, help='Mobilize partial or full robot team when executing a sub-task. "p" means that only those robots that execute a specific subtask can move and the rest will remain idle, acting as static obstacles, "p" means that the rest of robots not responsible for a specific subtask can move, mainly getting out of the way of moving robots.')
    return parser

print_red_on_cyan = lambda x: cprint(x, 'blue', 'on_red')
