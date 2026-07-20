from types import SimpleNamespace

import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.build import MaterialWithBuildMetadata
from mat3ra.made.tools.build.defective_structures.zero_dimensional.point_defect import (
    InterstitialPlacementMethodEnum,
    SubstitutionPlacementMethodEnum,
    VacancyPlacementMethodEnum,
)
from mat3ra.made.tools.build.defective_structures.zero_dimensional.point_defect.helpers import (
    create_defect_point_interstitial,
    create_defect_point_substitution,
    create_defect_point_vacancy,
    create_multiple_defects,
)
from mat3ra.made.tools.build.defective_structures.zero_dimensional.point_defect.types import PointDefectDict
from unit.fixtures.bulk import BULK_Si_CONVENTIONAL, BULK_Si_PRIMITIVE
from unit.fixtures.interface.zsl import GRAPHENE_NICKEL_INTERFACE
from unit.fixtures.point_defects import (
    INTERSTITIAL_DEFECT_BULK_PRIMITIVE_Si,
    INTERSTITIAL_VORONOI_DEFECT_BULK_PRIMITIVE_Si,
    MULTIPLE_POINT_DEFECTS_BULK_Si_CONVENTIONAL,
    SUBSTITUTION_DEFECT_BULK_PRIMITIVE_Si,
    VACANCY_DEFECT_BULK_PRIMITIVE_Si,
)
from unit.utils import assert_two_entities_deep_almost_equal, get_platform_specific_value

# The default comparison tolerance (atol=1e-9) in assert_two_entities_deep_almost_equal
# is too strict for the interstitial Voronoi placement method. Because Qhull/SciPy calculates
# different symmetrically equivalent vertices on different platforms/compilers, we define a
# custom coordinate tolerance (atol=1e-4) to verify that the generated coordinate is
# within a reasonable tolerance of any of the valid symmetrical Voronoi sites.
UPDATED_COORDINATE_TOLERANCE = 1e-4

FILM_LABEL = 1
SUBSTRATE_LABEL = 0
SUBSTITUTION_ELEMENT = "Ge"
INTERFACE_SUBSTITUTION_PLACEMENT_METHOD = SubstitutionPlacementMethodEnum.CLOSEST_SITE.value


def _film_atom_coordinate(material: Material) -> list:
    labels_by_id = {entry["id"]: entry["value"] for entry in material.basis.labels.to_dict()}
    for coordinate_entry in material.basis.coordinates.to_dict():
        if labels_by_id.get(coordinate_entry["id"]) == FILM_LABEL:
            return coordinate_entry["value"]
    raise ValueError("No film atom found in fixture material")


@pytest.mark.parametrize(
    "material_config, defect_params, expected_material_config",
    [
        (
            BULK_Si_PRIMITIVE,
            SimpleNamespace(
                type="vacancy",
                coordinate=[0.0, 0.0, 0.0],
                placement_method=VacancyPlacementMethodEnum.CLOSEST_SITE.value,
            ),
            VACANCY_DEFECT_BULK_PRIMITIVE_Si,
        ),
        (
            BULK_Si_PRIMITIVE,
            SimpleNamespace(
                type="substitution",
                coordinate=[0.0, 0.0, 0.0],
                element="Ge",
                placement_method=SubstitutionPlacementMethodEnum.CLOSEST_SITE.value,
            ),
            SUBSTITUTION_DEFECT_BULK_PRIMITIVE_Si,
        ),
        (
            BULK_Si_PRIMITIVE,
            SimpleNamespace(
                type="interstitial",
                coordinate=[0.5, 0.5, 0.5],
                element="C",
                placement_method=InterstitialPlacementMethodEnum.EXACT_COORDINATE.value,
            ),
            INTERSTITIAL_DEFECT_BULK_PRIMITIVE_Si,
        ),
        (
            BULK_Si_PRIMITIVE,
            SimpleNamespace(
                type="interstitial",
                coordinate=[0.25, 0.25, 0.5],
                element="Ge",
                placement_method=InterstitialPlacementMethodEnum.VORONOI_SITE.value,
            ),
            INTERSTITIAL_VORONOI_DEFECT_BULK_PRIMITIVE_Si,
        ),
    ],
)
def test_point_defect_helpers(material_config, defect_params, expected_material_config):
    crystal = Material.create(material_config)

    if defect_params.type == "vacancy":
        defect = create_defect_point_vacancy(crystal, defect_params.coordinate, defect_params.placement_method)
    elif defect_params.type == "substitution":
        defect = create_defect_point_substitution(
            crystal, defect_params.coordinate, defect_params.element, defect_params.placement_method
        )
    elif defect_params.type == "interstitial":
        defect = create_defect_point_interstitial(
            crystal, defect_params.coordinate, defect_params.element, defect_params.placement_method
        )
    else:
        raise ValueError(f"Unknown defect_type: {defect_params.type}")

    expected_material_config = get_platform_specific_value(expected_material_config)

    if (
        defect_params.type == "interstitial"
        and defect_params.placement_method == InterstitialPlacementMethodEnum.VORONOI_SITE.value
    ):
        # The interstitial atom is the 3rd atom (index 2)
        actual_coord = defect.basis.coordinates.values[2]
        allowed_coords = [[0.625, 0.625, 0.125], [0.625, 0.625, 0.625], [0.5, 0.5, 0.5]]
        assert any(
            np.allclose(actual_coord, allowed, atol=UPDATED_COORDINATE_TOLERANCE) for allowed in allowed_coords
        ), f"Voronoi coordinate {actual_coord} not in allowed list"
        if isinstance(expected_material_config, dict):
            expected_material_config["basis"]["coordinates"][2]["value"] = actual_coord
        else:
            expected_material_config.basis.coordinates.values[2] = actual_coord

    assert_two_entities_deep_almost_equal(defect, expected_material_config)


@pytest.mark.parametrize(
    "expected_label_count, expected_unique_labels",
    [(5, {SUBSTRATE_LABEL, FILM_LABEL})],
)
def test_create_defect_point_substitution_preserves_interface_labels(expected_label_count, expected_unique_labels):
    material = Material.create(GRAPHENE_NICKEL_INTERFACE)
    coordinate = _film_atom_coordinate(material)

    defect_material = create_defect_point_substitution(
        material, coordinate, SUBSTITUTION_ELEMENT, INTERFACE_SUBSTITUTION_PLACEMENT_METHOD
    )

    assert len(defect_material.basis.elements.values) == expected_label_count
    assert len(defect_material.basis.labels.values) == expected_label_count
    assert set(defect_material.basis.labels.values) == expected_unique_labels


@pytest.mark.parametrize(
    "material_config, defect_params_list, expected_material_config",
    [
        (
            BULK_Si_CONVENTIONAL,
            [
                SimpleNamespace(
                    defect_type="vacancy",
                    coordinate=[0.75, 0.70, 0.70],
                    placement_method=VacancyPlacementMethodEnum.CLOSEST_SITE.value,
                ),
                SimpleNamespace(
                    defect_type="interstitial",
                    coordinate=[0.25, 0.25, 0.2],
                    element="N",
                    placement_method=InterstitialPlacementMethodEnum.VORONOI_SITE.value,
                ),
                SimpleNamespace(
                    defect_type="substitution",
                    coordinate=[0.543, 0.543, 0.5],
                    element="Ge",
                    placement_method="closest_site",
                ),
            ],
            MULTIPLE_POINT_DEFECTS_BULK_Si_CONVENTIONAL,
        ),
    ],
)
def test_create_multiple_defects(material_config, defect_params_list, expected_material_config):
    material = MaterialWithBuildMetadata.create(material_config)

    defect_dicts = []
    for defect_params in defect_params_list:
        defect_data = {
            "type": defect_params.defect_type,
            "coordinate": defect_params.coordinate,
            "placement_method": defect_params.placement_method if hasattr(defect_params, "placement_method") else None,
            "element": defect_params.element if hasattr(defect_params, "element") else None,
        }

        defect_dict = PointDefectDict(**defect_data)

        defect_dicts.append(defect_dict)

    defects = create_multiple_defects(
        material=material,
        defect_dicts=defect_dicts,
    )
    assert_two_entities_deep_almost_equal(defects, expected_material_config)
