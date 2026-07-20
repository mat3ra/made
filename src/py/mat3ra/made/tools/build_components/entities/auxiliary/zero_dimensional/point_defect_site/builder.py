from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.made.basis import Basis, Coordinates

from ......build_components import MaterialWithBuildMetadata
from ..... import BaseSingleBuilder
from .configuration import PointDefectSiteConfiguration


class PointDefectSiteBuilder(BaseSingleBuilder):
    """
    Builder class for creating a material from a PointDefectSite configuration.
    """

    _ConfigurationType = PointDefectSiteConfiguration

    def _generate(self, configuration: PointDefectSiteConfiguration) -> MaterialWithBuildMetadata:
        if configuration.crystal is None:
            raise ValueError("Crystal configuration is required for PointDefectSiteBuilder")

        crystal = configuration.crystal
        basis = Basis(
            elements=ArrayWithIds(values=[], ids=[]),
            coordinates=Coordinates(values=[], ids=[]),
            units=crystal.basis.units,
            cell=crystal.basis.cell,
        )
        basis.add_atom(
            element=configuration.element.chemical_element,
            coordinate=configuration.coordinate,
            label=configuration.host_atom_label,
        )
        return MaterialWithBuildMetadata(name=crystal.name, lattice=crystal.lattice, basis=basis)
