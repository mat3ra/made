import pytest
from ase.build import bulk
from mat3ra.made.material import Material
from mat3ra.made.tools.build.compound_pristine_structures.two_dimensional.interface import get_optimal_film_displacement
from mat3ra.made.tools.build_components.metadata import MaterialWithBuildMetadata
from mat3ra.made.tools.calculate.calculators import InterfaceMaterialCalculator
from mat3ra.made.tools.convert import from_ase
from mat3ra.made.tools.convert.interface_parts_enum import InterfacePartsEnum
from mat3ra.made.tools.modify import (
    add_vacuum,
    filter_by_circle_projection,
    filter_by_ids,
    filter_by_label,
    filter_by_layers,
    filter_by_rectangle_projection,
    filter_by_sphere,
    filter_by_triangle_projection,
    interface_displace_part,
    interface_label_parts_by_elements,
    remove_vacuum,
    translate_to_z_level,
)
from mat3ra.made.tools.operations.core.unary import rotate
from mat3ra.utils import assertion as assertion_utils

from .fixtures.bulk import BULK_Si_CONVENTIONAL, BULK_Si_CONVENTIONAL_FILTERED
from .fixtures.interface.gr_ni_111_top_hcp import GRAPHENE_NICKEL_INTERFACE_TOP_HCP
from .fixtures.interface.zsl import GRAPHENE_NICKEL_INTERFACE
from .fixtures.slab import SI_SLAB_001_2_ATOMS, SI_SLAB_001_WITH_VACUUM
from .utils import assert_two_entities_deep_almost_equal

COMMON_PART = {
    "units": "crystal",
    "labels": [],
}

expected_basis_layers_section = {
    "elements": [
        {"id": 0, "value": "Si"},
        {"id": 3, "value": "Si"},
        {"id": 5, "value": "Si"},
        {"id": 6, "value": "Si"},
    ],
    "coordinates": [
        {"id": 0, "value": [0.5, 0.0, 0.0]},
        {"id": 3, "value": [0.25, 0.75, 0.25]},
        {"id": 5, "value": [0.75, 0.25, 0.25]},
        {"id": 6, "value": [0.0, 0.5, 0.0]},
    ],
    **COMMON_PART,
}

expected_basis_layers_cavity = {
    "elements": [
        {"id": 1, "value": "Si"},
        {"id": 2, "value": "Si"},
        {"id": 4, "value": "Si"},
        {"id": 7, "value": "Si"},
    ],
    "coordinates": [
        {"id": 1, "value": [0.25, 0.25, 0.75]},
        {"id": 2, "value": [0.5, 0.5, 0.5]},
        {"id": 4, "value": [0.0, 0.0, 0.5]},
        {"id": 7, "value": [0.75, 0.75, 0.75]},
    ],
    **COMMON_PART,
}


expected_basis_sphere_cluster = {
    "elements": [{"id": 2, "value": "Si"}],
    "coordinates": [{"id": 2, "value": [0.5, 0.5, 0.5]}],
    **COMMON_PART,
}

expected_basis_sphere_cavity = {
    "elements": [
        {"id": 0, "value": "Si"},
        {"id": 1, "value": "Si"},
        {"id": 3, "value": "Si"},
        {"id": 4, "value": "Si"},
        {"id": 5, "value": "Si"},
        {"id": 6, "value": "Si"},
        {"id": 7, "value": "Si"},
    ],
    "coordinates": [
        {"id": 0, "value": [0.5, 0.0, 0.0]},
        {"id": 1, "value": [0.25, 0.25, 0.75]},
        {"id": 3, "value": [0.25, 0.75, 0.25]},
        {"id": 4, "value": [0.0, 0.0, 0.5]},
        {"id": 5, "value": [0.75, 0.25, 0.25]},
        {"id": 6, "value": [0.0, 0.5, 0.0]},
        {"id": 7, "value": [0.75, 0.75, 0.75]},
    ],
    **COMMON_PART,
}

CRYSTAL_RADIUS = 0.25  # in crystal coordinates
CRYSTAL_CENTER_3D = [0.5, 0.5, 0.5]  # in crystal coordinates


def test_filter_by_ids():
    material = Material.create(BULK_Si_CONVENTIONAL)
    material_filtered = filter_by_ids(material, [0, 2])
    # Move to fixtures
    expected_material = Material.create(BULK_Si_CONVENTIONAL_FILTERED)
    assert_two_entities_deep_almost_equal(material_filtered.basis, expected_material.basis)


def test_filter_by_label():
    # TODO: create in fixtures
    substrate = bulk("Si", cubic=True)
    film = bulk("Cu", cubic=True)
    interface_atoms = substrate + film
    interface_atoms.set_tags([1] * len(substrate) + [2] * len(film))
    material_interface = Material.create(from_ase(interface_atoms))
    film_extracted = filter_by_label(material_interface, 2)
    film_material = Material.create(from_ase(film))

    # Ids of filtered elements will be missing, comparing the resulting values
    assert [el for el in film_material.basis.elements.values] == [el for el in film_extracted.basis.elements.values]


def test_filter_by_layers():
    material = Material.create(BULK_Si_CONVENTIONAL)
    section = filter_by_layers(material=material, central_atom_id=0, layer_thickness=3.0)
    cavity = filter_by_layers(material=material, central_atom_id=0, layer_thickness=3.0, invert_selection=True)
    assert_two_entities_deep_almost_equal(section.basis, expected_basis_layers_section)
    assert_two_entities_deep_almost_equal(cavity.basis, expected_basis_layers_cavity)


def test_filter_by_sphere():
    material = Material.create(BULK_Si_CONVENTIONAL)
    cluster = filter_by_sphere(material, center_coordinate=CRYSTAL_CENTER_3D, radius=CRYSTAL_RADIUS)
    cavity = filter_by_sphere(material, center_coordinate=CRYSTAL_CENTER_3D, radius=CRYSTAL_RADIUS, invert=True)
    assert_two_entities_deep_almost_equal(cluster.basis, expected_basis_sphere_cluster)
    assert_two_entities_deep_almost_equal(cavity.basis, expected_basis_sphere_cavity)


def test_filter_by_circle_projection():
    material = Material.create(BULK_Si_CONVENTIONAL)
    # Small cylinder in the middle of the cell containing the central atom will be removed -- the same as with sphere
    section = filter_by_circle_projection(material, 0.5, 0.5, CRYSTAL_RADIUS)
    cavity = filter_by_circle_projection(material, 0.5, 0.5, CRYSTAL_RADIUS, invert_selection=True)
    assert_two_entities_deep_almost_equal(section.basis, expected_basis_sphere_cluster)
    assert_two_entities_deep_almost_equal(cavity.basis, expected_basis_sphere_cavity)


def test_filter_by_rectangle_projection():
    material = Material.create(BULK_Si_CONVENTIONAL)
    # Default will contain all the atoms
    section = filter_by_rectangle_projection(material)
    assert_two_entities_deep_almost_equal(material.basis, section.basis)


def test_filter_by_triangle_projection():
    # Small prism in the middle of the cell containing the central atom will be removed -- the same as with sphere
    material = Material.create(BULK_Si_CONVENTIONAL)
    section = filter_by_triangle_projection(material, [0.4, 0.4], [0.4, 0.5], [0.5, 0.5])
    cavity = filter_by_triangle_projection(material, [0.4, 0.4], [0.4, 0.5], [0.5, 0.5], invert_selection=True)
    assert_two_entities_deep_almost_equal(section.basis, expected_basis_sphere_cluster)
    assert_two_entities_deep_almost_equal(cavity.basis, expected_basis_sphere_cavity)


def test_add_vacuum():
    material = Material.create(SI_SLAB_001_2_ATOMS)
    material_with_vacuum = add_vacuum(material, 5.0)
    assert_two_entities_deep_almost_equal(material_with_vacuum, SI_SLAB_001_WITH_VACUUM)


def test_remove_vacuum():
    material_with_vacuum = Material.create(SI_SLAB_001_WITH_VACUUM)
    vacuum = 7.368
    material_with_no_vacuum = remove_vacuum(material_with_vacuum, from_top=True, from_bottom=True, fixed_padding=0)
    expected_material = add_vacuum(material_with_no_vacuum, vacuum)
    # to compare correctly, we need to translate the expected material to the bottom
    # as it is effectively moved down when vacuum is removed (set to 0), use atol=1e-3 to account for the translation
    reference_material = Material.create(SI_SLAB_001_2_ATOMS)
    reference_material_translated_down = translate_to_z_level(reference_material, z_level="bottom")
    # compare absolute coordinates

    assert_two_entities_deep_almost_equal(expected_material, reference_material_translated_down, atol=1e-3)


@pytest.mark.parametrize(
    "material_config, rotations",
    [
        (
            SI_SLAB_001_2_ATOMS,
            [([0, 0, 1], 180), ([1, 0, 0], 180)],
        ),
        (
            SI_SLAB_001_WITH_VACUUM,
            [([1, 0, 0], 10)],
        ),
    ],
)
def test_rotate(material_config, rotations):
    material = Material.create(material_config)
    rotated_material = material
    for axis, angle in rotations:
        rotated_material = rotate(rotated_material, axis, angle)
    assertion_utils.assert_deep_almost_equal(
        material.basis.coordinates.values.sort(), rotated_material.basis.coordinates.values.sort()
    )
    assertion_utils.assert_deep_almost_equal(material.lattice, rotated_material.lattice)


def test_displace_interface():
    material = Material.create(GRAPHENE_NICKEL_INTERFACE)
    expected_coordinates = [
        {"id": 0, "value": [0.999999, 0.999999, 0]},
        {"id": 1, "value": [0.666665667, 0.666665667, 0.100960811]},
        {"id": 2, "value": [0.333332333, 0.333332333, 0.201921319]},
        {"id": 3, "value": [0.993759493, 0.093159552, 0.366525839]},
        {"id": 4, "value": [0.660425493, 0.759826552, 0.366525839]},
    ]

    expected_labels = GRAPHENE_NICKEL_INTERFACE["basis"]["labels"]
    displaced_material = interface_displace_part(
        material, [0.1, 0.2, 0.3], InterfacePartsEnum.FILM, use_cartesian_coordinates=True
    )
    assertion_utils.assert_deep_almost_equal(
        expected_coordinates, displaced_material.basis.coordinates.to_dict(), atol=1e-6
    )
    assertion_utils.assert_deep_almost_equal(expected_labels, displaced_material.basis.labels.to_dict())


def test_displace_interface_optimized():
    material = MaterialWithBuildMetadata.create(GRAPHENE_NICKEL_INTERFACE)
    expected_coordinates = [
        {"id": 0, "value": [0.999999, 0.999999, 3.03e-7]},
        {"id": 1, "value": [0.666665667, 0.666665667, 0.100960811]},
        {"id": 2, "value": [0.333332333, 0.333332333, 0.201921319]},
        {"id": 3, "value": [0.11112456, 0.181143574, 0.351561882]},
        {"id": 4, "value": [0.77779056, 0.847810574, 0.351561882]},
    ]
    expected_labels = GRAPHENE_NICKEL_INTERFACE["basis"]["labels"]

    optimal_displacement = get_optimal_film_displacement(
        material,
        calculator=InterfaceMaterialCalculator(),
        grid_size_xy=(10, 10),
        grid_range_x=(-0.5, 0.5),
        grid_range_y=(-0.5, 0.5),
        use_cartesian_coordinates=True,
    )
    displaced_material = interface_displace_part(material, optimal_displacement, use_cartesian_coordinates=True)
    assertion_utils.assert_deep_almost_equal(expected_coordinates, displaced_material.basis.coordinates.to_dict())
    assertion_utils.assert_deep_almost_equal(expected_labels, displaced_material.basis.labels.to_dict())


@pytest.mark.parametrize(
    "substrate_elements, expected_labels",
    [
        (["Ni"], GRAPHENE_NICKEL_INTERFACE_TOP_HCP["basis"]["labels"]),
        (
            ["C"],
            [
                {"id": label["id"], "value": 1 - label["value"]}
                for label in GRAPHENE_NICKEL_INTERFACE_TOP_HCP["basis"]["labels"]
            ],
        ),
    ],
)
def test_interface_label_parts_by_elements(substrate_elements, expected_labels):
    material = Material.create(GRAPHENE_NICKEL_INTERFACE_TOP_HCP)
    material.set_labels_from_list(None)
    labeled_material = interface_label_parts_by_elements(material, substrate_elements)
    assertion_utils.assert_deep_almost_equal(expected_labels, labeled_material.basis.labels.to_dict())
