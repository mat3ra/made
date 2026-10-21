from typing import cast

import numpy as np

from .build_parameters import GrainBoundaryLinearBuilderParameters
from .configuration import GrainBoundaryLinearConfiguration
from .network import Network, get_cell_size, get_grains, get_material_with_sites, get_monolayer, get_network
from .settling import get_settled_positions
from ....compound_pristine_structures.two_dimensional.interface import InterfaceBuilder
from ....pristine_structures.two_dimensional.slab.builder import SlabBuilder
from .....build_components import MaterialWithBuildMetadata
from .....utils import unwrap


class GrainBoundaryLinearBuilder(InterfaceBuilder):
    """
    Creates a linear grain boundary by stacking two materials along x or y direction; with core ring sizes, both lines
    get the boundary's bond network (network.py), settled to the material's bond length.
    """

    _ConfigurationType = GrainBoundaryLinearConfiguration
    _BuildParametersType = GrainBoundaryLinearBuilderParameters
    _DefaultBuildParameters = GrainBoundaryLinearBuilderParameters()

    def _generate(self, configuration: GrainBoundaryLinearConfiguration) -> MaterialWithBuildMetadata:
        material = super()._generate(configuration)
        if configuration.core_ring_sizes is None:
            return material
        monolayer = get_monolayer(SlabBuilder().get_material(configuration.stack_components[0]))
        supercell_matrices = [unwrap(component.xy_supercell_matrix) for component in configuration.stack_components]
        grains = get_grains(monolayer, supercell_matrices, configuration.xy_shift[0])
        # the slide of a configuration is one at which the network is unique
        network = cast(Network, get_network(monolayer, grains, configuration.core_ring_sizes))
        # the bond of a honeycomb of lattice constant a
        bond_length = np.linalg.norm(monolayer.lattice_vectors[0]) / np.sqrt(3)
        positions = get_settled_positions(network, get_cell_size(grains), bond_length)
        return get_material_with_sites(material, monolayer, positions, network.sites)

    def get_name_suffix(self, configuration: GrainBoundaryLinearConfiguration) -> str:
        angle_str = f"{configuration.actual_angle:.2f} degrees" if configuration.actual_angle is not None else ""
        return f"Linear Grain Boundary, {angle_str}"
