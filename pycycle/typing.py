from __future__ import annotations

from typing import Any, Protocol, Sequence


class ProblemLike(Protocol):
    """Protocol for OpenMDAO Problem objects used in viewers/utilities."""

    def get_val(self, name: str, units: str | None = None) -> Any: ...

    def set_val(self, name: str, value: Any, units: str | None = None) -> None: ...

    def run_model(self) -> None: ...

    @property
    def model(self) -> Any: ...


class GroupLike(Protocol):
    """Protocol for OpenMDAO Group-like objects used in connect helpers."""

    def pyc_connect_flow(
        self,
        fl_src: str,
        fl_target: str,
        connect_stat: bool = True,
        connect_tot: bool = True,
        connect_w: bool = True,
    ) -> None: ...


class SystemLike(Protocol):
    """Protocol for OpenMDAO System-like objects used for listing variables."""

    def list_outputs(
        self,
        out_stream: Any | None = None,
        return_format: str = "list",
        prom_name: bool = False,
    ) -> Sequence[tuple[str, dict[str, Any]]]: ...

    def list_inputs(
        self,
        out_stream: Any | None = None,
        return_format: str = "list",
        prom_name: bool = False,
    ) -> Sequence[tuple[str, dict[str, Any]]]: ...

    def set_val(self, name: str, val: Any, units: str | None = None) -> None: ...
