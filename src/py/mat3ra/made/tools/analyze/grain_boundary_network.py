from functools import cached_property
from typing import List, Tuple

import numpy as np
from mat3ra.esse.models.materials_category.defective_structures.one_dimensional.grain_boundary_linear.configuration import (  # noqa: E501
    GrainBoundaryCoreEnum,
)
from scipy.spatial import cKDTree

from .ring_network import BONDS_PER_SITE, HoneycombLattice, RingNetwork, RingNetworkAnalyzer, wrap_to_cell
from .rings import RING_CORE_SIZES

# a displacement that is a fixed periodic function of position, far above the platform noise of the coordinates, so
# the triangulation, and the co-circular groups found in it, are the same on every platform and for any atom order
TIE_BREAKING_DISPLACEMENT = 1e-5  # angstrom
TIE_BREAKING_WAVES = np.array([[3, 5], [7, 2]])
# sites on the edge of the rebuilt band (lattice sites can sit exactly there) stay, whatever the rounding
BAND_EDGE_TOLERANCE = 1e-3  # angstrom
REBUILT_BAND_WIDTH = 2.0  # lattice constants


class GrainBoundaryRingNetworkAnalyzer(RingNetworkAnalyzer):
    """
    Ring network of a honeycomb grain boundary (graphene, h-BN, MoS2): grains labelled 0 and 1 stacked along x without
    a gap, the lines at x = 0 and x = the width of grain 0. The ring centres are the hexagon centres of both grains, for
    any slide of the second grain along the lines; a site takes the atoms of its sublattice in the grain holding most of
    its ring centres. Sites within REBUILT_BAND_WIDTH lattice constants of either line are rebuilt; every other site
    keeps its stacked position.
    """

    supercell_matrices: List[List[List[int]]]

    @cached_property
    def cell(self) -> np.ndarray:
        return np.diag(self.lattice_vectors).copy()

    @cached_property
    def grain_widths(self) -> np.ndarray:
        areas = np.abs([np.linalg.det(matrix) for matrix in self.supercell_matrices])
        return self.cell[0] * areas / areas.sum()

    @cached_property
    def line_positions(self) -> List[float]:
        return [0.0, float(self.grain_widths[0])]

    @cached_property
    def site_grains(self) -> np.ndarray:
        return np.array(self.material.basis.labels.values)[self.site_first_atoms]

    @cached_property
    def grain_lattices(self) -> List[HoneycombLattice]:
        return [self.get_grain_lattice(grain) for grain in (0, 1)]

    def get_grain_lattice(self, grain: int) -> HoneycombLattice:
        """Vectors from the grain's supercell matrix; sublattice 1 is the nearest other site of the same grain."""
        sites = np.where(self.site_grains == grain)[0]
        offsets = self.site_positions[sites] - self.site_positions[sites[0]]
        offsets -= np.round(offsets / self.cell) * self.cell
        nearest = 1 + np.argmin(np.linalg.norm(offsets[1:], axis=1))
        return HoneycombLattice(
            vectors=np.linalg.inv(self.supercell_matrices[grain]) @ np.diag([self.grain_widths[grain], self.cell[1]]),
            origin=self.site_positions[sites[0]],
            sublattice_offset=offsets[nearest],
            sublattice_sites=(sites[0], sites[nearest]),
        )

    @cached_property
    def site_distance(self) -> float:
        return float(np.linalg.norm(self.grain_lattices[0].sublattice_offset))

    @cached_property
    def kept_sites(self) -> np.ndarray:
        """Sites at REBUILT_BAND_WIDTH lattice constants or more from both lines."""
        x_values = self.site_positions[:, 0]
        distances = np.min([np.abs(x_values - line) for line in self.line_positions + [self.cell[0]]], axis=0)
        return np.where(distances >= REBUILT_BAND_WIDTH * np.sqrt(3) * self.site_distance - BAND_EDGE_TOLERANCE)[0]

    @cached_property
    def grain_hexagon_centers(self) -> Tuple[np.ndarray, np.ndarray]:
        """Hexagon centres of each grain inside its own supercell, one per site of sublattice 0, and their grains."""
        centers = []
        for grain, lattice in enumerate(self.grain_lattices):
            sites = self.site_positions[self.site_grains == grain]
            points = sites[lattice.get_sublattices(sites) == 0] - lattice.sublattice_offset
            start = self.line_positions[grain]
            points[:, 0] = start + wrap_to_cell(points[:, 0] - start, self.grain_widths[grain])
            centers.append(wrap_to_cell(points, self.cell))
        return np.vstack(centers), np.repeat([0, 1], [len(points) for points in centers])

    def get_ring_centers(self, slide: float) -> np.ndarray:
        """Hexagon centres with the second grain slid by `slide` along y, moved by the tie-breaking displacement."""
        centers, grains = self.grain_hexagon_centers
        centers = wrap_to_cell(centers + np.outer(grains, [0.0, slide]), self.cell)
        return centers + TIE_BREAKING_DISPLACEMENT * np.sin(2 * np.pi * (centers / self.cell) @ TIE_BREAKING_WAVES.T)

    def get_slid_network(self, slide: float, core: GrainBoundaryCoreEnum) -> RingNetwork:
        """Network of the hexagon centres, the second grain slid by `slide` along y, for the rings of `core`."""
        return self.get_network(self.get_ring_centers(slide), RING_CORE_SIZES[core.value])

    def get_small_cell_error(self) -> ValueError:
        return ValueError(
            f"The cell is too short along the boundary ({self.cell[1]:.3f} angstrom) for its periodic ring "
            "network; use a multiple of the boundary vectors"
        )

    def get_grains(self, network: RingNetwork) -> np.ndarray:
        """The grain holding most of the ring centres around each site."""
        ring_grains = self.grain_hexagon_centers[1][network.bond_rings.reshape(-1, BONDS_PER_SITE)]
        return (ring_grains.sum(axis=1) >= 2).astype(int)

    def get_column_sites(self, network: RingNetwork, slide: float = 0.0) -> np.ndarray:
        """The stacked site whose atoms each site takes: its sublattice's in its grain, the second slid by `slide`."""
        grains = self.get_grains(network)
        sublattices = self.get_sublattices(network.positions, grains, slide)
        return np.array([lattice.sublattice_sites for lattice in self.grain_lattices])[grains, sublattices]

    def get_sublattices(self, positions: np.ndarray, grains: np.ndarray, slide: float) -> np.ndarray:
        """
        Sublattice of each site in the lattice of its grain, the second grain slid by `slide`, read at the site's image
        inside that grain: the stacked cell's width is a lattice vector of neither grain.
        """
        middles = np.array(self.line_positions) + self.grain_widths / 2
        images_across = np.round((positions[:, 0] - middles[grains]) / self.cell[0])
        unslid_positions = positions - np.outer(images_across, [self.cell[0], 0.0]) - np.outer(grains, [0.0, slide])
        return np.choose(grains, [lattice.get_sublattices(unslid_positions) for lattice in self.grain_lattices])

    def get_kept_vertices(self, positions: np.ndarray) -> np.ndarray:
        kept_positions = wrap_to_cell(self.site_positions[self.kept_sites], self.cell)
        return cKDTree(wrap_to_cell(positions, self.cell), boxsize=self.cell).query(kept_positions)[1]
