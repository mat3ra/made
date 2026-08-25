from typing import List, Optional, Tuple, Union

from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum
from mat3ra.esse.models.materials_category.pristine_structures.two_dimensional.slab import SlabConfigurationSchema
from mat3ra.made.material import Material
from .termination_utils import select_slab_termination

from .....analyze.lattice_planes import CrystalLatticePlanesMaterialAnalyzer
from .....build_components.entities.reusable.two_dimensional.atomic_layers_unique_repeated.configuration import (
    AtomicLayersUniqueRepeatedConfiguration,
)
from .....build_components.metadata import MaterialWithBuildMetadata
from .....build_components.operations.core.combinations.stack.configuration import StackConfiguration
from .....build_components.entities.core.two_dimensional.vacuum.configuration import VacuumConfiguration
from .....build_components.entities.auxiliary.two_dimensional.termination import Termination


class SlabConfiguration(StackConfiguration, SlabConfigurationSchema):
    type: str = "SlabConfiguration"
    stack_components: List[Union[AtomicLayersUniqueRepeatedConfiguration, VacuumConfiguration]]  # No Materials!
    direction: AxisEnum = AxisEnum.z

    termination_top: Optional[Termination] = None
    termination_bottom: Optional[Termination] = None

    @property
    def number_of_layers(self):
        return self.atomic_layers.number_of_repetitions

    @property
    def vacuum(self):
        return self.vacuum_configuration.size

    @property
    def atomic_layers(self):
        return self.stack_components[0]

    @property
    def vacuum_configuration(self) -> VacuumConfiguration:
        return self.stack_components[1]

    def set_vacuum(self, vacuum: float) -> None:
        vacuum_configuration = self.vacuum_configuration
        vacuum_configuration.size = vacuum
        self.stack_components[1] = vacuum_configuration

    @classmethod
    def from_parameters(
        cls,
        material_or_dict: Union[Material, dict],
        miller_indices: Tuple[int, int, int],
        number_of_layers: int,
        termination_top_formula: Optional[str] = None,
        termination_bottom_formula: Optional[str] = None,
        vacuum: float = 10.0,
        use_conventional_cell: bool = True,
    ) -> "SlabConfiguration":
        """
        Creates a SlabConfiguration from the given parameters.
        Args:
            material_or_dict (Union[Material, dict]): Material or dictionary representation of the material.
            miller_indices (Tuple[int, int, int]): Miller indices for the slab surface.
            number_of_layers (int): Number of atomic layers in the slab, in the number of unit cells.
            termination_top_formula (Optional[str]): Formula of the top termination to use for the slab (i.e. "SrTiO").
            termination_bottom_formula (Optional[str]): Formula of the bottom termination to use for the slab.

            vacuum (float): Size of the vacuum layer in Angstroms.
            use_conventional_cell (bool): Whether the slab is built in the conventional cell.
                Stored on the configuration and applied at build time; `crystal` always keeps
                the material that was passed in.

        Returns:
            SlabConfiguration: The created slab configuration.
        """
        if isinstance(material_or_dict, dict):
            material = MaterialWithBuildMetadata.create(material_or_dict)
        else:
            material = material_or_dict

        crystal_lattice_planes_analyzer = CrystalLatticePlanesMaterialAnalyzer(
            material=material, miller_indices=miller_indices
        )
        terminations = crystal_lattice_planes_analyzer.terminations
        termination_top = select_slab_termination(terminations, termination_top_formula)
        termination_bottom = select_slab_termination(terminations, termination_bottom_formula)

        atomic_layers_repeated_configuration = AtomicLayersUniqueRepeatedConfiguration(
            crystal=material,
            miller_indices=miller_indices,
            use_conventional_cell=use_conventional_cell,
            termination_top=termination_top,
            termination_bottom=termination_bottom,
            number_of_repetitions=number_of_layers,
        )

        vacuum_configuration = VacuumConfiguration(size=vacuum, crystal=None, direction=AxisEnum.z)

        return cls(
            stack_components=[atomic_layers_repeated_configuration, vacuum_configuration],
            direction=AxisEnum.z,
        )
