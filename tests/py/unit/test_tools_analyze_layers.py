from typing import Final

import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.other import get_atom_indices_by_layer, get_atom_indices_in_bottom_layers
from unit.fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP

INTERFACE: Final = Material.create(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)  # Ni 0-2, C 3-4 (same height)
SUBSTRATE_ATOMS: Final = [0, 1, 2]


def test_atom_indices_grouped_by_layer():
    assert get_atom_indices_by_layer(INTERFACE) == [[0], [1], [2], [3, 4]]


def test_bottom_one_layer_of_the_substrate():
    assert get_atom_indices_in_bottom_layers(INTERFACE, 1, SUBSTRATE_ATOMS) == [0]


def test_bottom_two_layers_of_the_substrate():
    assert get_atom_indices_in_bottom_layers(INTERFACE, 2, SUBSTRATE_ATOMS) == [0, 1]


def test_bottom_layer_among_all_atoms():
    assert get_atom_indices_in_bottom_layers(INTERFACE, 1) == [0]


def test_bottom_layers_of_no_atoms_is_empty():
    assert get_atom_indices_in_bottom_layers(INTERFACE, 1, []) == []


def test_zero_layers_raises():
    with pytest.raises(ValueError):
        get_atom_indices_in_bottom_layers(INTERFACE, 0)
