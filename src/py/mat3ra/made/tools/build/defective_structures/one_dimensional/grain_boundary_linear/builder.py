"""Stacks the two grains and, with a core, rebuilds the band along each line (stack, reconstruct, settle)."""
from typing import cast

from .build_parameters import GrainBoundaryLinearBuilderParameters
from .configuration import GrainBoundaryLinearConfiguration
from ....compound_pristine_structures.two_dimensional.interface import InterfaceBuilder
from .....build_components import MaterialWithBuildMetadata
from .....build_components.operations.core.modifications.reconstruct import RingNetworkReconstruction
from .....utils import unwrap


class GrainBoundaryLinearBuilder(InterfaceBuilder):
    """
    Creates a linear grain boundary by stacking two materials along x or y direction; with core ring sizes, the bands
    along both lines rebuilt as their ring network (RingNetworkReconstruction).
    """

    _ConfigurationType = GrainBoundaryLinearConfiguration
    _BuildParametersType = GrainBoundaryLinearBuilderParameters
    _DefaultBuildParameters = GrainBoundaryLinearBuilderParameters()

    def _generate(self, configuration: GrainBoundaryLinearConfiguration) -> MaterialWithBuildMetadata:
        material = super()._generate(configuration)
        if configuration.core_ring_sizes is None:
            return material
        build_parameters = cast(GrainBoundaryLinearBuilderParameters, self.build_parameters)
        return RingNetworkReconstruction(
            material=material,
            supercell_matrices=[unwrap(component.xy_supercell_matrix) for component in configuration.stack_components],
            band_width=build_parameters.band_width,
            settling_tolerance=build_parameters.settling_tolerance,
        ).reconstructed_material

    def get_name_suffix(self, configuration: GrainBoundaryLinearConfiguration) -> str:
        angle_str = f"{configuration.actual_angle:.2f} degrees" if configuration.actual_angle is not None else ""
        return f"Linear Grain Boundary, {angle_str}"
