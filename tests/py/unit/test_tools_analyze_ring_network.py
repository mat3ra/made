import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.ring_network import RingNetworkAnalyzer, wrap_to_cell
from mat3ra.made.tools.analyze.rings import HEXAGON_SIZE, get_periodic_images
from mat3ra.made.tools.helpers import create_supercell
from mat3ra.standata.materials import Materials
from scipy.spatial import cKDTree

MOLYBDENUM_DISULFIDE_2D = Materials.get_by_name_and_categories("Molybdenum_Disulfide", "2D")
# standata's crystal coordinates have six decimals, so its sites are that far from the ideal honeycomb
SITE_TOLERANCE = 1e-5  # angstrom


@pytest.mark.parametrize(
    "material_config, supercell_matrix, expected_ring_sizes",
    [(MOLYBDENUM_DISULFIDE_2D, [[3, 0, 0], [0, 3, 0], [0, 0, 1]], [6] * 9)],
)
def test_ring_network_analyzer(material_config, supercell_matrix, expected_ring_sizes):
    analyzer = RingNetworkAnalyzer(material=create_supercell(Material.create(material_config), supercell_matrix))
    lattice_vectors = analyzer.lattice_vectors
    centers = wrap_to_cell(analyzer.ring_centers @ np.linalg.inv(lattice_vectors), 1.0) @ lattice_vectors
    network = analyzer.get_network(centers, [HEXAGON_SIZE])
    site_images = get_periodic_images(analyzer.site_positions, lattice_vectors)
    distances, images = cKDTree(site_images).query(network.positions)

    assert sorted((images % len(analyzer.site_positions)).tolist()) == list(range(len(analyzer.site_positions)))
    assert distances.max() < SITE_TOLERANCE
    assert np.bincount(network.bond_rings).tolist() == expected_ring_sizes
