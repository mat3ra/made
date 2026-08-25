from typing import Any, Dict, List

import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.helpers import (
    create_atomic_layers,
    create_defect_point_vacancy,
    create_grain_boundary_linear,
    create_grain_boundary_planar,
    create_interface_commensurate,
    create_interface_twisted,
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
    "slab": lambda crystal: create_slab(crystal=crystal, miller_indices=MILLER_INDICES, number_of_layers=3),
    "interface_zsl": lambda crystal: create_interface_zsl(
        substrate_crystal=crystal, film_crystal=crystal, max_area=50.0
    ),
    "interface_commensurate": lambda crystal: create_interface_commensurate(
        material=crystal, target_angle=13.0, angle_tolerance=0.5, max_repetition_int=5
    ),
    "grain_boundary_planar": lambda crystal: create_grain_boundary_planar(
        phase_1_material=crystal,
        phase_1_miller_indices=MILLER_INDICES,
        phase_2_miller_indices=(0, 1, 1),
        max_area=100.0,
    ),
    "grain_boundary_linear": lambda crystal: create_grain_boundary_linear(
        material=crystal, target_angle=13.0, angle_tolerance=0.5, max_repetition_int=5, gap=1.0
    ),
    "point_defect_vacancy": lambda crystal: create_defect_point_vacancy(crystal, [0.0, 0.0, 0.0], "closest_site"),
}


def get_recorded_source_crystals(node: Any) -> List[Dict[str, Any]]:
    """Crystals recorded next to Miller indices, plus defect hosts. A vacuum's is a built intermediate."""
    if isinstance(node, list):
        return [crystal for item in node for crystal in get_recorded_source_crystals(item)]
    if not isinstance(node, dict):
        return []
    crystals = []
    collected = set()
    if isinstance(node.get("crystal"), dict) and "miller_indices" in node:
        crystals.append(node["crystal"])
        collected.add("crystal")
    if node.get("merge_components"):
        crystals.append(node["merge_components"][0])
        collected.add("merge_components")
    # Do not descend into what was just collected: an input with its own build history would
    # otherwise contribute the crystals nested inside it.
    return crystals + [
        found for key, value in node.items() if key not in collected for found in get_recorded_source_crystals(value)
    ]


@pytest.mark.parametrize("build", BUILDERS.values(), ids=BUILDERS.keys())
def test_recorded_crystal_is_the_input(build):
    material = Material.create(BULK_Ni_PRIMITIVE_WITH_ID)

    built = build(material)

    recorded = get_recorded_source_crystals(built.model_dump()["metadata"]["build"])
    assert recorded
    for crystal in recorded:
        assert_two_entities_deep_almost_equal(crystal, material)


@pytest.mark.parametrize("material_config, expected_number_of_atoms, expected_gamma", [(BULK_Ni_PRIMITIVE, 8, 90.0)])
def test_create_interface_twisted_uses_conventional_cell(material_config, expected_number_of_atoms, expected_gamma):
    # TwistedNanoribbonsInterfaceAnalyzer reads atomic_layers.crystal as geometry and never calls
    # the builder, so this helper has to conventionalize up front. Moving that into the builder
    # collapses the result onto the primitive one -- 8 atoms to 1, gamma 90 to 120.
    crystal = Material.create(material_config)

    interface = create_interface_twisted(material1=crystal, material2=crystal, angle=10.0, use_conventional_cell=True)

    assert len(interface.basis.elements.values) == expected_number_of_atoms
    assert interface.lattice.gamma == pytest.approx(expected_gamma)


@pytest.mark.parametrize("material_config, expected_material_config", [(BULK_Ni_PRIMITIVE, ATOMIC_LAYERS_NI_001)])
def test_create_atomic_layers(material_config, expected_material_config):
    material = Material.create(material_config)
    termination = get_slab_terminations(material, MILLER_INDICES)[0]

    atomic_layers = create_atomic_layers(material, MILLER_INDICES, termination=termination)

    assert_two_entities_deep_almost_equal(atomic_layers, expected_material_config)
