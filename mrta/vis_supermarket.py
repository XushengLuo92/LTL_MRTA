"""Supermarket demos share the presentation renderer used by other cases."""
from .vis import plot_workspace, plot_workspace_helper, vis as render


def vis(workspace, robot_path, robot_pre_suf_time, ap, **options):
    options.setdefault('output', 'data/mapp.mp4')
    options.setdefault('title', 'Multi-robot coordination / Supermarket')
    return render('supermarket', workspace, robot_path, robot_pre_suf_time, ap, **options)
