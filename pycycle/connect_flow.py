import warnings

from pycycle.typing import GroupLike


def connect_flow(
    group: GroupLike,
    fl_src: str,
    fl_target: str,
    connect_stat: bool = True,
    connect_tot: bool = True,
    connect_w: bool = True,
) -> None:
    """Connect flow variables (deprecated)."""

    warnings.simplefilter('always', DeprecationWarning)
    warnings.warn(
        "Deprecation warning: `connect_flow` function is deprecated. "
        "Use the `pyc_connect_flow` method from `Cycle` class instead."
    )
    warnings.simplefilter('ignore', DeprecationWarning)

    group.pyc_connect_flow(fl_src, fl_target, connect_stat, connect_tot, connect_w)
