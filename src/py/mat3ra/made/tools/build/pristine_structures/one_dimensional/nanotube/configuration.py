from pydantic import Field

from mat3ra.made.tools.build_components.entities.reusable.base_builder import BaseConfigurationPydantic
from ...two_dimensional.nanoribbon.configuration import NanoribbonConfiguration


class NanotubeConfiguration(BaseConfigurationPydantic):
    """
    Configuration for building a single-walled nanotube from a nanoribbon.

    The nanotube is created by rolling a nanoribbon into a cylinder along the y-axis (width direction).
    The x-axis of the nanoribbon becomes the tube axis. The vacuum_around_tube parameter controls
    the vacuum region around the nanotube in the cross-sectional plane.

    Args:
        nanoribbon: The nanoribbon configuration to roll into a nanotube.
        vacuum_around_tube: The vacuum region around the tube cross-section in Angstroms.
    """

    type: str = "NanotubeConfiguration"
    nanoribbon: NanoribbonConfiguration
    vacuum_around_tube: float = Field(default=10.0, description="Vacuum around the tube cross-section in Angstroms.")
