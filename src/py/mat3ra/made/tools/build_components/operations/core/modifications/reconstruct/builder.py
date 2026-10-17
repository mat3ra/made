"""
The band along each line of two stacked grains rebuilt as their ring network: each site takes the atoms of the stacked
column it maps onto, then the sites are settled to the bond length.
"""
from typing import Type, cast

import numpy as np
from mat3ra.code.array_with_ids import ArrayWithIds
from mat3ra.esse.models.material import BasisUnitsEnum
from mat3ra.made.basis import Basis
from mat3ra.made.basis.coordinates import Coordinates
from mat3ra.made.tools.build_components.entities.reusable.base_builder import BaseSingleBuilder

from ......analyze.ring_network import BONDS_PER_SITE, RingNetwork, RingNetworkAnalyzer
from ......analyze.utils import wrap_to_cell
from ..... import MaterialWithBuildMetadata
from .build_parameters import RingNetworkReconstructionBuilderParameters
from .configuration import RingNetworkReconstructionConfiguration
from .network_settling import NetworkSettling


class RingNetworkReconstructionBuilder(BaseSingleBuilder):
    """
    Rebuilds the band within `band_width` lattice constants of each line as the ring network of both grains
    (RingNetworkAnalyzer): each site takes the atoms of the stacked site of its sublattice in the grain of most of its
    centres; the sites are then settled to the bond length, every stacked atom outside the bands kept.
    """

    _ConfigurationType: Type[RingNetworkReconstructionConfiguration] = RingNetworkReconstructionConfiguration
    _BuildParametersType: Type[RingNetworkReconstructionBuilderParameters] = RingNetworkReconstructionBuilderParameters
    _DefaultBuildParameters: RingNetworkReconstructionBuilderParameters = RingNetworkReconstructionBuilderParameters()

    def _generate(self, configuration: RingNetworkReconstructionConfiguration) -> MaterialWithBuildMetadata:
        analyzer = RingNetworkAnalyzer(
            material=configuration.material,
            supercell_matrices=configuration.supercell_matrices,
            band_width=cast(RingNetworkReconstructionBuilderParameters, self.build_parameters).band_width,
        )
        network = analyzer.get_network(slide=0.0)
        return self.get_assembled_material(analyzer, network, self.get_settled_positions(analyzer, network))

    def get_settled_positions(self, analyzer: RingNetworkAnalyzer, network: RingNetwork) -> np.ndarray:
        """Positions of the rebuilt sites settled to the bond length, every other site fixed, wrapped into the cell."""
        settling = NetworkSettling(
            positions=network.positions,
            bonds=(
                np.repeat(np.arange(len(network.positions)), BONDS_PER_SITE),
                network.neighbors.ravel(),
                network.vectors.reshape(-1, 2),
            ),
            movable=network.is_rebuilt,
            bond_length=analyzer.bond_length,
            tolerance=cast(RingNetworkReconstructionBuilderParameters, self.build_parameters).settling_tolerance,
        )
        return wrap_to_cell(settling.settled_positions[network.is_rebuilt], analyzer.cell)

    def get_assembled_material(
        self, analyzer: RingNetworkAnalyzer, network: RingNetwork, positions: np.ndarray
    ) -> MaterialWithBuildMetadata:
        """The stacked atoms outside the bands, then the atoms of each rebuilt site's column at its settled position."""
        kept_atoms = np.flatnonzero(
            analyzer.get_line_distances(analyzer.sites.atom_positions[:, 0]) >= analyzer.band_edge
        )
        columns = analyzer.get_site_columns(network, slide=0.0)[network.is_rebuilt]
        grains = analyzer.get_site_grains(network)[network.is_rebuilt]
        material = analyzer.material.clone()
        material.to_cartesian()
        coordinates = np.array(material.basis.coordinates.values)
        column_atoms = [np.flatnonzero(analyzer.sites.atom_site_indices == column) for column in columns]
        rebuilt_atoms = np.concatenate(column_atoms)
        sites = np.repeat(np.arange(len(columns)), [len(atoms) for atoms in column_atoms])
        atoms = np.concatenate([kept_atoms, rebuilt_atoms])
        rebuilt_coordinates = np.column_stack([positions[sites], coordinates[rebuilt_atoms, 2]])
        material.basis = Basis(
            elements=ArrayWithIds.from_values(np.array(material.basis.elements.values)[atoms].tolist()),
            coordinates=Coordinates.from_values(np.vstack([coordinates[kept_atoms], rebuilt_coordinates]).tolist()),
            units=BasisUnitsEnum.cartesian,
            cell=material.basis.cell,
            labels=ArrayWithIds.from_values(
                np.concatenate([np.array(material.basis.labels.values)[kept_atoms], grains[sites]]).tolist()
            ),
        )
        material.to_crystal()
        return material
