from typing import Type, Union

from ..build.compound_pristine_structures.two_dimensional.interface.base.build_parameters import (
    InterfaceBuilderParameters,
)
from ..build.compound_pristine_structures.two_dimensional.interface.base.configuration import InterfaceConfiguration
from ..build.pristine_structures.two_dimensional.slab.configuration import SlabConfiguration
from ..build.pristine_structures.two_dimensional.slab_strained_supercell.configuration import (
    SlabStrainedSupercellConfiguration,
)
from ..build_components.metadata import MaterialWithBuildMetadata
from ..convert.interface_parts_enum import INTERFACE_LABELS_MAP
from .build_metadata_analyzer import BuildMetadataAnalyzer


class InterfaceMaterialAnalyzer(
    BuildMetadataAnalyzer[InterfaceConfiguration, InterfaceBuilderParameters],
):
    configuration_cls: Type[InterfaceConfiguration] = InterfaceConfiguration
    build_parameters_cls: Type[InterfaceBuilderParameters] = InterfaceBuilderParameters

    @property
    def substrate_slab_configuration(self) -> Union[SlabStrainedSupercellConfiguration, SlabConfiguration]:
        return self.build_configuration.substrate_configuration

    @property
    def film_slab_configuration(self) -> Union[SlabStrainedSupercellConfiguration, SlabConfiguration]:
        return self.build_configuration.film_configuration

    def get_bulk_crystal(self, part: str = "substrate") -> dict:
        if part not in INTERFACE_LABELS_MAP:
            raise ValueError(f"Unknown interface part '{part}'. Use 'substrate' or 'film'.")
        slab_configuration = self.substrate_slab_configuration if part == "substrate" else self.film_slab_configuration
        crystal = slab_configuration.atomic_layers.crystal
        if crystal is None:
            raise ValueError(f"No bulk crystal for {part} in interface build metadata.")
        return crystal if isinstance(crystal, dict) else crystal.to_dict()


def get_interface_configuration(interface: MaterialWithBuildMetadata) -> InterfaceConfiguration:
    return InterfaceMaterialAnalyzer(material=interface).build_configuration


def get_interface_bulk_crystal(interface: MaterialWithBuildMetadata, part: str = "substrate") -> dict:
    return InterfaceMaterialAnalyzer(material=interface).get_bulk_crystal(part=part)
