import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.build.pristine_structures.one_dimensional.nanotube import create_nanotube

from .fixtures.monolayer import GRAPHENE
from .fixtures.nanotube.armchair import GRAPHENE_NANOTUBE_ARMCHAIR
from .fixtures.nanotube.zigzag import GRAPHENE_NANOTUBE_ZIGZAG
from .utils import assert_two_entities_deep_almost_equal


@pytest.mark.parametrize(
    "material_config, width, length, vacuum_around_tube, miller_indices_2d, expected_nanotube",
    [
        (GRAPHENE, 4, 4, 10.0, (0, 1), GRAPHENE_NANOTUBE_ZIGZAG),
        (GRAPHENE, 4, 4, 10.0, (1, 1), GRAPHENE_NANOTUBE_ARMCHAIR),
    ],
)
def test_build_nanotube(
    material_config, width, length, vacuum_around_tube, miller_indices_2d, expected_nanotube
):
    material = Material.create(material_config)

    nanotube = create_nanotube(
        material=material,
        miller_indices_2d=miller_indices_2d,
        width=width,
        length=length,
        vacuum_around_tube=vacuum_around_tube,
    )

    assert_two_entities_deep_almost_equal(nanotube, expected_nanotube)


def test_nanotube_cylindrical_geometry():
    """All atoms in the nanotube should be at the same radial distance from the tube axis."""
    material = Material.create(GRAPHENE)
    nanotube = create_nanotube(
        material=material,
        miller_indices_2d=(0, 1),
        width=4,
        length=4,
        vacuum_around_tube=10.0,
    )

    n2 = nanotube.clone()
    n2.to_cartesian()
    coords = np.array(n2.basis.coordinates.values)

    center_y = nanotube.lattice.b / 2
    center_z = nanotube.lattice.c / 2
    radii = np.sqrt((coords[:, 1] - center_y) ** 2 + (coords[:, 2] - center_z) ** 2)

    # All atoms should be at the same radius
    assert np.allclose(radii, radii[0], atol=1e-3), (
        f"Atoms are not all at the same radius: min={radii.min():.4f}, max={radii.max():.4f}"
    )


def test_nanotube_cross_section_is_square():
    """The cross-sectional lattice dimensions (b and c) should be equal."""
    material = Material.create(GRAPHENE)
    nanotube = create_nanotube(
        material=material,
        miller_indices_2d=(0, 1),
        width=4,
        length=4,
        vacuum_around_tube=10.0,
    )

    assert abs(nanotube.lattice.b - nanotube.lattice.c) < 1e-6, (
        f"Cross-section is not square: b={nanotube.lattice.b}, c={nanotube.lattice.c}"
    )


def test_nanotube_atom_count_matches_nanoribbon():
    """The nanotube should have the same number of atoms as the underlying nanoribbon."""
    from mat3ra.made.tools.build.pristine_structures.two_dimensional.nanoribbon import create_nanoribbon

    material = Material.create(GRAPHENE)
    width, length = 4, 4

    nanoribbon = create_nanoribbon(
        material=material,
        miller_indices_2d=(0, 1),
        width=width,
        length=length,
        vacuum_width=0.0,
        vacuum_length=0.0,
    )
    nanotube = create_nanotube(
        material=material,
        miller_indices_2d=(0, 1),
        width=width,
        length=length,
        vacuum_around_tube=10.0,
    )

    assert nanotube.basis.number_of_atoms == nanoribbon.basis.number_of_atoms, (
        f"Atom count mismatch: nanotube={nanotube.basis.number_of_atoms}, "
        f"nanoribbon={nanoribbon.basis.number_of_atoms}"
    )
