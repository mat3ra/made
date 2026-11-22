from mat3ra.esse.models.core.primitive.axis_3d_names_enum import AxisEnum

from ..... import MaterialWithBuildMetadata
from ...two_dimensional.vacuum.builder import VacuumBuilder
from ...two_dimensional.vacuum.configuration import VacuumConfiguration
from .configuration import AtomAtCoordinateConfiguration


class AtomAtCoordinateBuilder(VacuumBuilder):
    _ConfigurationType = AtomAtCoordinateConfiguration

    def _generate(self, configuration: AtomAtCoordinateConfiguration) -> MaterialWithBuildMetadata:
        if not configuration.crystal:
            raise ValueError("Crystal must be provided for AtomAtCoordinateConfiguration")
        vacuum_configuration = VacuumConfiguration(
            crystal=configuration.crystal,
            size=configuration.crystal.lattice.c,
            direction=AxisEnum.z,
        )
        new_material = super()._generate(vacuum_configuration)
        new_material.basis.add_atom(
            element=configuration.element.chemical_element.value,
            coordinate=configuration.coordinate,
        )
        return new_material
