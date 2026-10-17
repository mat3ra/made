import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.helpers import RingsMaterialAnalyzer
from mat3ra.standata.materials import Materials

from .fixtures.grain_boundary import GRAIN_BOUNDARY_LINEAR_BORON_NITRIDE_5_7
from .utils import assert_two_entities_deep_almost_equal

GRAPHENE_2D = Materials.get_by_name_and_categories("Graphene", "2D")
TYPE_III_LINE = {"cores": [[5, 7, 5, 7]], "same_size_pairs": 0, "homo_bonds": {"B-B": 1, "N-N": 1}}
NO_DEFECT_LINE: dict = {"cores": [], "same_size_pairs": 0, "homo_bonds": {}}


@pytest.mark.parametrize(
    "material_config, expected_ring_sizes, expected_arrangements",
    [
        (GRAPHENE_2D, [6], [NO_DEFECT_LINE]),
        (GRAIN_BOUNDARY_LINEAR_BORON_NITRIDE_5_7, [5] * 4 + [6] * 44 + [7] * 4, [TYPE_III_LINE, TYPE_III_LINE]),
    ],
)
def test_rings_material_analyzer(material_config, expected_ring_sizes, expected_arrangements):
    analyzer = RingsMaterialAnalyzer(material=Material.create(material_config))
    line_positions = np.arange(len(expected_arrangements)) * analyzer.lattice_vectors[0, 0] / len(expected_arrangements)
    arrangements = [arrangement.model_dump() for arrangement in analyzer.get_line_arrangements(list(line_positions))]
    assert sorted(analyzer.ring_sizes.tolist()) == expected_ring_sizes
    assert_two_entities_deep_almost_equal(arrangements, expected_arrangements)
