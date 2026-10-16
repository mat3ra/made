import numpy as np
from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.material import BasisUnitsEnum
from mat3ra.made.basis import Basis
from mat3ra.made.basis.coordinates import Coordinates

from .build_parameters import GrainBoundaryLinearBuilderParameters
from .configuration import GrainBoundaryLinearConfiguration
from .settling import NetworkSettling
from ....compound_pristine_structures.two_dimensional.interface import InterfaceBuilder
from .....analyze.grain_boundary_network import GrainBoundaryRingNetworkAnalyzer, get_tolerant_ranks, wrap_to_cell
from .....build_components import MaterialWithBuildMetadata
from .....utils import unwrap

# coordinates closer than this count as equal when ordering atoms, so the order does not follow their last digits
ATOM_ORDER_TOLERANCE = 1e-3  # angstrom


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
        ring_network = network.get_network(0.0, configuration.core)
        movable = np.ones(len(ring_network.positions), bool)
        movable[network.get_kept_vertices(ring_network.positions)] = False
        settling = NetworkSettling(
            positions=ring_network.positions,
            bonds=ring_network.bonds,
            movable=movable,
            site_distance=network.site_distance,
        )
        rebuilt_positions = wrap_to_cell(settling.settled_positions[movable], network.cell)
        column_sites = network.get_column_sites(ring_network.grains[movable], ring_network.sublattices[movable])
        return self._get_assembled_material(network, rebuilt_positions, column_sites, ring_network.grains[movable])

    def _get_assembled_material(
        self,
        network: GrainBoundaryRingNetworkAnalyzer,
        positions: np.ndarray,
        column_sites: np.ndarray,
        grains: np.ndarray,
    ) -> MaterialWithBuildMetadata:
        """The kept atoms and the column atoms at each rebuilt position, ordered by grain, then y, then x, then z."""
        material = network.material.clone()
        material.to_cartesian()
        coordinates = np.array(material.basis.coordinates.values)
        elements, labels = np.array(material.basis.elements.values), np.array(material.basis.labels.values)
        kept_atoms = np.where(np.isin(network.atom_site_indices, network.kept_sites))[0]
        columns = [np.where(network.atom_site_indices == site)[0] for site in column_sites]
        column_atoms, repeats = np.concatenate(columns), [len(column) for column in columns]
        added_coordinates = np.column_stack([np.repeat(positions, repeats, axis=0), coordinates[column_atoms, 2]])
        all_coordinates = np.vstack([coordinates[kept_atoms], added_coordinates])
        all_labels = np.concatenate([labels[kept_atoms], np.repeat(grains, repeats)])
        ranks = [get_tolerant_ranks(all_coordinates[:, axis], ATOM_ORDER_TOLERANCE) for axis in (2, 0, 1)]
        order = np.lexsort([*ranks, all_labels])
        material.basis = Basis(
            elements=ArrayWithIds.from_values(elements[np.concatenate([kept_atoms, column_atoms])][order].tolist()),
            coordinates=Coordinates.from_values(all_coordinates[order].tolist()),
            units=BasisUnitsEnum.cartesian,
            cell=material.basis.cell,
            labels=ArrayWithIds.from_values(all_labels[order].tolist()),
        )
        material.to_crystal()
        return material

    def get_name_suffix(self, configuration: GrainBoundaryLinearConfiguration) -> str:
        angle_str = f"{configuration.actual_angle:.2f} degrees" if configuration.actual_angle is not None else ""
        return f"Linear Grain Boundary, {angle_str}"
