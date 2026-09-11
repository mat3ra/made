from typing import Final, List, Optional, Tuple

import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.other import get_atom_indices_by_layer, get_atom_indices_in_bottom_layers
from unit.fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP

INTERFACE: Final = Material.create(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)  # Ni 0-2, C 3-4 (same height)
SUBSTRATE_ATOMS: Final = [0, 1, 2]

GET_ATOM_INDICES_BY_LAYER_CASES = [
    (INTERFACE, [[0], [1], [2], [3, 4]]),
]


@pytest.mark.parametrize("material, expected_layers", GET_ATOM_INDICES_BY_LAYER_CASES)
def test_get_atom_indices_by_layer(material, expected_layers):
    assert get_atom_indices_by_layer(material) == expected_layers


GET_ATOM_INDICES_IN_BOTTOM_LAYERS_CASES: List[Tuple[Material, int, Optional[List[int]], List[int]]] = [
    (INTERFACE, 1, SUBSTRATE_ATOMS, [0]),
    (INTERFACE, 2, SUBSTRATE_ATOMS, [0, 1]),
    (INTERFACE, 1, None, [0]),
    (INTERFACE, 1, [], []),
]


@pytest.mark.parametrize(
    "material, layer_count, atom_indices, expected_indices", GET_ATOM_INDICES_IN_BOTTOM_LAYERS_CASES
)
def test_get_atom_indices_in_bottom_layers(material, layer_count, atom_indices, expected_indices):
    assert get_atom_indices_in_bottom_layers(material, layer_count, atom_indices) == expected_indices


def test_get_atom_indices_in_bottom_layers_invalid():
    with pytest.raises(ValueError):
        get_atom_indices_in_bottom_layers(INTERFACE, 0)
