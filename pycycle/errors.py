"""Custom exception types for pyCycle configuration and flow errors."""

from __future__ import annotations


class PyCycleError(Exception):
    """Base exception for pyCycle errors."""


class CycleConfigurationError(PyCycleError):
    """Raised for invalid cycle configuration or lifecycle usage."""


class FlowConnectionError(PyCycleError):
    """Raised when flow connections or ports are invalid or missing."""


class MapConfigurationError(PyCycleError):
    """Raised for invalid map configuration inputs."""
