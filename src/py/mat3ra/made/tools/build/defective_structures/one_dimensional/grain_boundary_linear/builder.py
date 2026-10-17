"""
A linear grain boundary of two grains of a monolayer stacked along x. With a core: matched along the boundary line
(GrainBoundaryLinearAnalyzer: matching vectors, rectangular supercells, the slide), stacked, and the band along each
line rebuilt as the ring network of both grains' hexagon centres (RingNetworkAnalyzer: Delaunay triangulation, ties
split by one rule), each site taking the atoms of its column, then settled (RingNetworkReconstructionBuilder).
"""
from typing import cast

from .build_parameters import GrainBoundaryLinearBuilderParameters
from .configuration import GrainBoundaryLinearConfiguration
from ....compound_pristine_structures.two_dimensional.interface import InterfaceBuilder
from .....build_components import MaterialWithBuildMetadata
from .....build_components.operations.core.modifications.reconstruct import (
    RingNetworkReconstructionBuilder,
    RingNetworkReconstructionConfiguration,
)
from .....utils import unwrap


class GrainBoundaryLinearBuilder(InterfaceBuilder):
    """
    Creates a linear grain boundary by stacking two materials along x or y direction; with core ring sizes, the bands
    along both lines rebuilt as their ring network.
    """

    _ConfigurationType = GrainBoundaryLinearConfiguration
    _BuildParametersType = GrainBoundaryLinearBuilderParameters
    _DefaultBuildParameters = GrainBoundaryLinearBuilderParameters()

    def _generate(self, configuration: GrainBoundaryLinearConfiguration) -> MaterialWithBuildMetadata:
        material = super()._generate(configuration)
        if configuration.core_ring_sizes is None:
            return material
        reconstruction = RingNetworkReconstructionConfiguration(
            material=material,
            supercell_matrices=[unwrap(component.xy_supercell_matrix) for component in configuration.stack_components],
        )
        # generated, not built: the boundary's history holds its own step only
        builder = RingNetworkReconstructionBuilder(
            build_parameters=cast(GrainBoundaryLinearBuilderParameters, self.build_parameters)
        )
        return builder._generate(reconstruction)

    def get_name_suffix(self, configuration: GrainBoundaryLinearConfiguration) -> str:
        angle_str = f"{configuration.actual_angle:.2f} degrees" if configuration.actual_angle is not None else ""
        return f"Linear Grain Boundary, {angle_str}"
