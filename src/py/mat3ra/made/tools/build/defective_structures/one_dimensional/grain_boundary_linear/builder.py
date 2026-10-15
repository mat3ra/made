from .build_parameters import GrainBoundaryLinearBuilderParameters
from .configuration import GrainBoundaryLinearConfiguration
from .reconstruction import GrainBoundaryCoreReconstruction
from ....compound_pristine_structures.two_dimensional.interface import InterfaceBuilder
from .....build_components import MaterialWithBuildMetadata
from .....utils import unwrap


class GrainBoundaryLinearBuilder(InterfaceBuilder):
    """
    Creates a linear grain boundary by stacking two materials along x or y direction.
    With a core, the sites near both lines are rebuilt into it (GrainBoundaryCoreReconstruction).
    """

    _ConfigurationType = GrainBoundaryLinearConfiguration
    _BuildParametersType = GrainBoundaryLinearBuilderParameters
    _DefaultBuildParameters = GrainBoundaryLinearBuilderParameters()

    def _generate(self, configuration: GrainBoundaryLinearConfiguration) -> MaterialWithBuildMetadata:
        material = super()._generate(configuration)
        if configuration.core is None:
            return material
        supercell_matrices = [unwrap(component.xy_supercell_matrix) for component in configuration.stack_components]
        return GrainBoundaryCoreReconstruction(material=material, supercell_matrices=supercell_matrices).get_material()

    def get_name_suffix(self, configuration: GrainBoundaryLinearConfiguration) -> str:
        angle_str = f"{configuration.actual_angle:.2f} degrees" if configuration.actual_angle is not None else ""
        return f"Linear Grain Boundary, {angle_str}"
