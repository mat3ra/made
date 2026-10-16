import numpy as np
from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.material import BasisUnitsEnum
from mat3ra.made.basis import Basis
from mat3ra.made.basis.coordinates import Coordinates
from scipy.spatial import cKDTree

from .build_parameters import GrainBoundaryLinearBuilderParameters
from .configuration import GrainBoundaryLinearConfiguration
from ....compound_pristine_structures.two_dimensional.interface import InterfaceBuilder
from .....analyze.grain_boundary_network import GrainBoundaryRingNetworkAnalyzer
from .....analyze.ring_network import wrap_to_cell
from .....analyze.rings import RingNetwork, get_periodic_images
from .....build_components import MaterialWithBuildMetadata
from .....build_components.operations.core.modifications.settle import NetworkSettling
from .....utils import unwrap


class GrainBoundaryLinearBuilder(InterfaceBuilder):
    """
    Creates a linear grain boundary by stacking two materials along x or y direction.
    With a core, the sites near both lines become the settled vertices of the ring network
    (GrainBoundaryRingNetworkAnalyzer), each with the atoms of its sublattice's column.
    """

    _ConfigurationType = GrainBoundaryLinearConfiguration
    _BuildParametersType = GrainBoundaryLinearBuilderParameters
    _DefaultBuildParameters = GrainBoundaryLinearBuilderParameters()

    def _generate(self, configuration: GrainBoundaryLinearConfiguration) -> MaterialWithBuildMetadata:
        material = super()._generate(configuration)
        if configuration.core is None:
            return material
        supercell_matrices = [unwrap(component.xy_supercell_matrix) for component in configuration.stack_components]
        network = GrainBoundaryRingNetworkAnalyzer(material=material, supercell_matrices=supercell_matrices)
        ring_network = network.get_slid_network(0.0, configuration.core.value)
        vertex_images = get_periodic_images(ring_network.positions, network.lattice_vectors)
        kept_images = cKDTree(vertex_images).query(network.site_positions[network.kept_sites])[1]
        kept_vertices = kept_images % len(ring_network.positions)
        movable = np.ones(len(ring_network.positions), bool)
        movable[kept_vertices] = False
        settling = NetworkSettling(
            positions=ring_network.positions,
            bonds=ring_network.bonds,
            movable=movable,
            bond_length=network.site_distance,
        )
        sites = network.get_column_sites(ring_network, 0.0)
        sites[kept_vertices] = network.kept_sites
        positions = wrap_to_cell(settling.settled_positions, network.cell)
        return self._get_assembled_material(network, ring_network, sites, positions, movable)

    def _get_assembled_material(
        self,
        network: GrainBoundaryRingNetworkAnalyzer,
        ring_network: RingNetwork,
        sites: np.ndarray,
        positions: np.ndarray,
        movable: np.ndarray,
    ) -> MaterialWithBuildMetadata:
        """
        The atoms of each network site, the sites by grain and integer key (get_site_keys), a site's atoms up its column
        (they lie a bond length or more apart in z): a kept site's own atoms, a rebuilt site's column's at its settled
        position.
        """
        material = network.material.clone()
        material.to_cartesian()
        coordinates = np.array(material.basis.coordinates.values)
        elements, labels = np.array(material.basis.elements.values), np.array(material.basis.labels.values)
        grains = network.get_grains(ring_network)
        order = np.lexsort([*network.get_site_keys(ring_network).T[::-1], grains])
        columns = [np.where(network.atom_site_indices == sites[vertex])[0] for vertex in order]
        columns = [column[np.argsort(coordinates[column, 2])] for column in columns]
        atoms, vertices = np.concatenate(columns), np.repeat(order, [len(column) for column in columns])
        rebuilt = movable[vertices]
        xy = np.where(rebuilt[:, None], positions[vertices], coordinates[atoms, :2])
        material.basis = Basis(
            elements=ArrayWithIds.from_values(elements[atoms].tolist()),
            coordinates=Coordinates.from_values(np.column_stack([xy, coordinates[atoms, 2]]).tolist()),
            units=BasisUnitsEnum.cartesian,
            cell=material.basis.cell,
            labels=ArrayWithIds.from_values(np.where(rebuilt, grains[vertices], labels[atoms]).tolist()),
        )
        material.to_crystal()
        return material

    def get_name_suffix(self, configuration: GrainBoundaryLinearConfiguration) -> str:
        angle_str = f"{configuration.actual_angle:.2f} degrees" if configuration.actual_angle is not None else ""
        return f"Linear Grain Boundary, {angle_str}"
