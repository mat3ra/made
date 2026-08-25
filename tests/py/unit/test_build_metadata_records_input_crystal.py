from typing import Any, Dict, List

import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.helpers import (
    create_atomic_layers,
    create_defect_point_vacancy,
    create_grain_boundary_linear,
    create_grain_boundary_planar,
    create_interface_commensurate,
    create_interface_zsl,
    create_slab,
    get_slab_terminations,
)

from .fixtures.bulk import BULK_Ni_PRIMITIVE
from .fixtures.slab import ATOMIC_LAYERS_NI_001
from .utils import assert_two_entities_deep_almost_equal

MILLER_INDICES = (0, 0, 1)
# Ni primitive differs from its own conventional cell, so a builder that conventionalizes fails.
BULK_Ni_PRIMITIVE_WITH_ID: Dict[str, Any] = {**BULK_Ni_PRIMITIVE, "_id": "platform-id-abc"}

BUILDERS = {
    "slab": lambda c: create_slab(crystal=c, miller_indices=MILLER_INDICES, number_of_layers=3),
    "interface_zsl": lambda c: create_interface_zsl(substrate_crystal=c, film_crystal=c, max_area=50.0),
    "interface_commensurate": lambda c: create_interface_commensurate(
        material=c, target_angle=13.0, angle_tolerance=0.5, max_repetition_int=5
    ),
    "grain_boundary_planar": lambda c: create_grain_boundary_planar(
        phase_1_material=c, phase_1_miller_indices=MILLER_INDICES, phase_2_miller_indices=(0, 1, 1), max_area=100.0
    ),
    "grain_boundary_linear": lambda c: create_grain_boundary_linear(
        material=c, target_angle=13.0, angle_tolerance=0.5, max_repetition_int=5, gap=1.0
    ),
    "point_defect_vacancy": lambda c: create_defect_point_vacancy(c, [0.0, 0.0, 0.0], "closest_site"),
}


def get_recorded_source_crystals(node: Any) -> List[Dict[str, Any]]:
    """Crystals recorded next to Miller indices, plus defect hosts. A vacuum's is a built intermediate."""
    if isinstance(node, list):
        return [crystal for item in node for crystal in get_recorded_source_crystals(item)]
    if not isinstance(node, dict):
        return []
    crystals = []
    if isinstance(node.get("crystal"), dict) and "miller_indices" in node:
        crystals.append(node["crystal"])
    if node.get("merge_components"):
        crystals.append(node["merge_components"][0])
    return crystals + [c for value in node.values() for c in get_recorded_source_crystals(value)]


@pytest.mark.parametrize("build", BUILDERS.values(), ids=BUILDERS.keys())
def test_recorded_crystal_is_the_input(build):
    material = Material.create(BULK_Ni_PRIMITIVE_WITH_ID)

    built = build(material)

    recorded = get_recorded_source_crystals(built.model_dump()["metadata"]["build"])
    assert recorded
    for crystal in recorded:
        assert_two_entities_deep_almost_equal(crystal, material)


@pytest.mark.parametrize("material_config, expected_material_config", [(BULK_Ni_PRIMITIVE, ATOMIC_LAYERS_NI_001)])
def test_create_atomic_layers(material_config, expected_material_config):
    material = Material.create(material_config)
    termination = get_slab_terminations(material, MILLER_INDICES)[0]

    atomic_layers = create_atomic_layers(material, MILLER_INDICES, termination=termination)

    assert_two_entities_deep_almost_equal(atomic_layers, expected_material_config)
