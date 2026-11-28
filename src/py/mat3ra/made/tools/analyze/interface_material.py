from typing import Type, Union

import numpy as np
from mat3ra.esse.models.core.abstract.matrix_3x3 import Matrix3x3Schema

from ..build.compound_pristine_structures.two_dimensional.interface.base.build_parameters import (
    InterfaceBuilderParameters,
)
from ..build.compound_pristine_structures.two_dimensional.interface.base.configuration import InterfaceConfiguration
from ..build.pristine_structures.two_dimensional.slab.build_parameters import SlabBuilderParameters
from ..build.pristine_structures.two_dimensional.slab.configuration import SlabConfiguration
from ..build.pristine_structures.two_dimensional.slab_strained_supercell.builder import SlabStrainedSupercellBuilder
from ..build.pristine_structures.two_dimensional.slab_strained_supercell.configuration import (
    SlabStrainedSupercellConfiguration,
)
from ..build_components.metadata import MaterialWithBuildMetadata
from ..convert.interface_parts_enum import INTERFACE_LABELS_MAP, InterfacePartsEnum
from ..operations.reusable.unary import strain_to_match_lattice
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


def create_interface_bulk_cell(
    interface: MaterialWithBuildMetadata, part: InterfacePartsEnum
) -> MaterialWithBuildMetadata:
    """
    The part's strained crystal as a periodic cell of one repetition: the crystal coordinates of the unstrained cell
    with the crystal's own c = alpha a + beta b + h n, on the strained part's a', b' and alpha a' + beta b' + h n'.
    """
    slab_configuration = get_interface_configuration(interface).stack_components[part]
    slab_configuration.atomic_layers.number_of_repetitions = 1
    strained_cell = SlabStrainedSupercellBuilder().get_material(slab_configuration)
    slab_configuration.strain_matrix = Matrix3x3Schema(root=np.eye(3).tolist())
    oriented_cell = SlabStrainedSupercellBuilder(
        build_parameters=SlabBuilderParameters(use_orthogonal_c=False)
    ).get_material(slab_configuration)
    a, b, c = np.array(oriented_cell.lattice.vector_arrays)
    normal = np.cross(a, b) / np.linalg.norm(np.cross(a, b))
    alpha, beta, _ = np.linalg.solve(np.array([a, b, normal]).T, c)
    strained_a, strained_b, strained_c = np.array(strained_cell.lattice.vector_arrays)
    strained_cell.set_lattice_vectors(strained_a, strained_b, strained_c + alpha * strained_a + beta * strained_b)
    return strain_to_match_lattice(oriented_cell, strained_cell)
