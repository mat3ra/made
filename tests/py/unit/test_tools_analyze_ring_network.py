import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.ring_network import RingNetworkAnalyzer, wrap_to_lattice
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
    network = analyzer.get_network(wrap_to_lattice(analyzer.ring_centers, analyzer.lattice_vectors), [HEXAGON_SIZE])
    rings_analyzer = analyzer.get_rings_analyzer(network, analyzer.get_column_sites(network))
    site_images = get_periodic_images(analyzer.site_positions, analyzer.lattice_vectors)
    distances, images = cKDTree(site_images).query(network.positions)
    sites = images % len(analyzer.site_positions)

    assert sorted(sites.tolist()) == list(range(len(analyzer.site_positions)))
    assert distances.max() < SITE_TOLERANCE
    assert rings_analyzer.ring_sizes.tolist() == expected_ring_sizes
    assert rings_analyzer.site_species.tolist() == analyzer.site_species[sites].tolist()
