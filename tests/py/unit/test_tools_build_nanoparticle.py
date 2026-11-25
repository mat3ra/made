import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze import BaseMaterialAnalyzer
from mat3ra.made.tools.build.pristine_structures.zero_dimensional.nanoparticle import (
    NanoparticleShapesEnum,
    create_nanoparticle_by_shape,
    create_nanoparticle_from_material,
)
from mat3ra.made.tools.entities.coordinate import SphereCoordinateCondition
from unit.fixtures.bulk import BULK_Si_PRIMITIVE
from unit.fixtures.nanoparticle import SI_NANOPARTICLE_SPHERE
from unit.utils import assert_two_entities_deep_almost_equal


@pytest.mark.parametrize(
    "material_config, condition, expected_material_config",
    [
        (
            BULK_Si_PRIMITIVE,
            SphereCoordinateCondition(radius=6.0),
            SI_NANOPARTICLE_SPHERE,
        ),
    ],
)
def test_create_nanoparticle_by_condition(material_config, condition, expected_material_config):
    material = Material.create(material_config)
    nanoparticle = create_nanoparticle_from_material(
        material, condition=condition, center_around_atom=True, use_cartesian_coordinates=True
    )

    assert_two_entities_deep_almost_equal(nanoparticle, expected_material_config)


@pytest.mark.parametrize(
    "material_config, shape, parameters, expected_nearest_neighbor_distance",
    [
        (BULK_Si_PRIMITIVE, NanoparticleShapesEnum.ICOSAHEDRON, {"noshells": 3}, 3.867),
        (BULK_Si_PRIMITIVE, NanoparticleShapesEnum.OCTAHEDRON, {"length": 5, "cutoff": 2}, 3.867),
        (BULK_Si_PRIMITIVE, NanoparticleShapesEnum.DECAHEDRON, {"p": 3, "q": 2, "r": 0}, 3.867),
    ],
)
def test_create_nanoparticle_by_shape(material_config, shape, parameters, expected_nearest_neighbor_distance):
    material = Material.create(material_config)
    nanoparticle = create_nanoparticle_by_shape(material, shape, parameters)
    nearest_neighbor_distance = BaseMaterialAnalyzer(material=nanoparticle).pairwise_distances.min()
    assert np.isclose(nearest_neighbor_distance, expected_nearest_neighbor_distance, atol=1e-3)
