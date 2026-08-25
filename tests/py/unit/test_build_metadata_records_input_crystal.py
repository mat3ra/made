"""
The crystal recorded in build metadata must be the material that was passed in.

A bulk reference resolved from build metadata (surface energy, defect formation energy,
interfacial energy) is only comparable with a Total Energy job run on the same cell, so
primitive input has to stay primitive and conventional input has to stay conventional.
"""

from typing import Any, Dict, List

import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.analyze.lattice_planes import CrystalLatticePlanesMaterialAnalyzer
from mat3ra.made.tools.analyze.slab import SlabMaterialAnalyzer
from mat3ra.made.tools.build import MaterialWithBuildMetadata
from mat3ra.made.tools.build.pristine_structures.two_dimensional.slab import SlabBuilder
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
from .fixtures.slab import SI_CONVENTIONAL_SLAB_001
from .utils import assert_two_entities_deep_almost_equal

INPUT_ID = "platform-id-abc"
MILLER_INDICES = (0, 0, 1)


def make_input(config: Dict[str, Any]) -> Material:
    # _id names one exact material, so it has to survive alongside the hashes.
    return Material.create({**config, "_id": INPUT_ID})


def get_conventional_lattice_hash(crystal: Material) -> str:
    analyzer = CrystalLatticePlanesMaterialAnalyzer(material=crystal, miller_indices=MILLER_INDICES)
    return analyzer.material_with_conventional_lattice.hash


def collect_source_crystals(node: Any, crystals: List[Dict[str, Any]]) -> None:
    """
    A source crystal is one recorded next to Miller indices (a lattice-planes configuration) or as
    the host of a defect configuration. A vacuum's `crystal` is a built intermediate, not a source.
    """
    if isinstance(node, dict):
        if isinstance(node.get("crystal"), dict) and "miller_indices" in node:
            crystals.append(node["crystal"])
        if node.get("merge_components"):
            # Defect configurations record the host material first; the rest are the defect parts.
            crystals.append(node["merge_components"][0])
        for value in node.values():
            collect_source_crystals(value, crystals)
    elif isinstance(node, list):
        for value in node:
            collect_source_crystals(value, crystals)


def get_recorded_source_crystals(material: Material) -> List[Dict[str, Any]]:
    crystals: List[Dict[str, Any]] = []
    collect_source_crystals(material.model_dump()["metadata"]["build"], crystals)
    return crystals


# Every input is a cell whose conventional form differs from itself, so each case can actually fail
# the criterion it asserts.
BUILDERS = {
    "slab": lambda c: create_slab(crystal=c, miller_indices=MILLER_INDICES, number_of_layers=3),
    "interface_zsl": lambda c: create_interface_zsl(substrate_crystal=c, film_crystal=c, max_area=50.0),
    "interface_commensurate": lambda c: create_interface_commensurate(
        material=c, target_angle=13.0, angle_tolerance=0.5, max_repetition_int=5
    ),
    "grain_boundary_planar": lambda c: create_grain_boundary_planar(
        phase_1_material=c,
        phase_1_miller_indices=MILLER_INDICES,
        phase_2_miller_indices=(0, 1, 1),
        max_area=100.0,
    ),
    "grain_boundary_linear": lambda c: create_grain_boundary_linear(
        material=c, target_angle=13.0, angle_tolerance=0.5, max_repetition_int=5, gap=1.0
    ),
    # Already correct before this ticket -- here as a regression guard.
    "point_defect_vacancy": lambda c: create_defect_point_vacancy(c, [0.0, 0.0, 0.0], "closest_site"),
}


@pytest.mark.parametrize("build", BUILDERS.values(), ids=BUILDERS.keys())
def test_recorded_crystal_is_the_input(build):
    crystal = make_input(BULK_Ni_PRIMITIVE)
    assert get_conventional_lattice_hash(crystal) != crystal.hash, "input must differ from its conventional cell"

    recorded = get_recorded_source_crystals(build(crystal))

    assert recorded, "builder recorded no source crystal"
    for entry in recorded:
        assert entry["hash"] == crystal.hash
        assert entry["scaledHash"] == crystal.scaled_hash
        assert entry["_id"] == INPUT_ID


def test_twisted_interface_still_honours_use_conventional_cell():
    # TwistedNanoribbonsInterfaceAnalyzer reads atomic_layers.crystal as geometry and never calls
    # the builder, so create_interface_twisted has to conventionalize up front. If these two ever
    # produce the same structure, that transform was moved somewhere the analyzer cannot see it.
    crystal = Material.create(BULK_Ni_PRIMITIVE)

    from_conventional = create_interface_twisted(
        material1=crystal, material2=crystal, angle=10.0, use_conventional_cell=True
    )
    from_input = create_interface_twisted(material1=crystal, material2=crystal, angle=10.0, use_conventional_cell=False)

    assert from_conventional.hash != from_input.hash


def test_create_atomic_layers_does_not_conventionalize_the_input():
    # create_atomic_layers builds the configuration directly, where the schema default is True.
    # Without the explicit False it would silently start conventionalizing.
    crystal = Material.create(BULK_Ni_PRIMITIVE)
    conventional = CrystalLatticePlanesMaterialAnalyzer(
        material=crystal, miller_indices=MILLER_INDICES
    ).material_with_conventional_lattice
    termination = get_slab_terminations(crystal, MILLER_INDICES)[0]

    assert (
        create_atomic_layers(crystal, MILLER_INDICES, termination=termination).hash
        != create_atomic_layers(conventional, MILLER_INDICES, termination=termination).hash
    )


def test_configuration_saved_before_this_change_does_not_round_trip():
    # Before this change `from_parameters` never forwarded the flag, so EVERY stored configuration
    # reads "use_conventional_cell": true -- including slabs built from the primitive cell. Now that
    # _generate honors the flag, those stored configurations rebuild conventionalized instead of
    # reproducing themselves. Accepted consequence of fixing the ticket's root cause 2, pinned here
    # so it is a recorded decision rather than a surprise: rebuild such a slab from its crystal,
    # not from its metadata.
    crystal = Material.create(BULK_Ni_PRIMITIVE)
    slab = create_slab(crystal=crystal, miller_indices=MILLER_INDICES, number_of_layers=3, use_conventional_cell=False)
    stored = slab.model_dump(mode="json")
    stored["metadata"]["build"][-1]["configuration"]["stack_components"][0]["use_conventional_cell"] = True

    rebuilt = SlabBuilder().get_material(
        SlabMaterialAnalyzer(material=MaterialWithBuildMetadata.create(stored)).build_configuration
    )

    conventionalized = create_slab(
        crystal=crystal, miller_indices=MILLER_INDICES, number_of_layers=3, use_conventional_cell=True
    )
    assert rebuilt.hash != slab.hash
    assert rebuilt.hash == conventionalized.hash


def test_rebuilding_a_slab_from_its_own_metadata_is_stable():
    # A slab saved before this change records the conventional cell next to use_conventional_cell
    # True; conventionalizing an already-conventional cell has to be a no-op.
    slab = MaterialWithBuildMetadata.create(SI_CONVENTIONAL_SLAB_001)

    rebuilt = SlabBuilder().get_material(SlabMaterialAnalyzer(material=slab).build_configuration)

    assert_two_entities_deep_almost_equal(rebuilt.basis, slab.basis)
    assert_two_entities_deep_almost_equal(rebuilt.lattice, slab.lattice)
