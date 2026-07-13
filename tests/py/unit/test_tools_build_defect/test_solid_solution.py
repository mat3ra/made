import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.build.defective_structures.three_dimensional.solid_solution.helpers import (
    create_solid_solution,
)
from mat3ra.standata.materials import Materials

BULK_HfO2 = Materials.get_by_name_first_match("HfO2")


def _min_nearest_neighbor_distance(material, element):
    material.to_crystal()
    coords = np.array(material.basis.coordinates.values)
    lv = np.array(material.lattice.vector_arrays)
    idx = [i for i, e in enumerate(material.basis.elements.values) if e == element]
    sub = coords[idx]
    min_d = np.inf
    for i in range(len(sub)):
        for j in range(i + 1, len(sub)):
            delta = sub[i] - sub[j]
            delta -= np.round(delta)
            min_d = min(min_d, np.linalg.norm(delta @ lv))
    return min_d


def test_create_solid_solution_uniform_element_counts():
    material = Material.create(BULK_HfO2)
    result = create_solid_solution(material, "Hf", "Zr", 0.5, seed=42, site_selection_method="uniform")
    elements = result.basis.elements.values
    assert elements == ["Hf", "Hf", "O", "O", "O", "O", "O", "O", "O", "O", "Zr", "Zr"]


@pytest.mark.parametrize(
    "concentration, expected_zr, expected_hf",
    [
        (0.0, 0, 4),
        (0.25, 1, 3),
        (0.5, 2, 2),
        (1.0, 4, 0),
    ],
)
def test_create_solid_solution_concentration(concentration, expected_zr, expected_hf):
    material = Material.create(BULK_HfO2)
    result = create_solid_solution(material, "Hf", "Zr", concentration, seed=42, site_selection_method="uniform")
    elements = result.basis.elements.values
    assert elements.count("Zr") == expected_zr
    assert elements.count("Hf") == expected_hf


@pytest.mark.parametrize(
    "concentration, expected_min_distance",
    [
        (0.1, 4.5),
        (0.2, 3.5),
        (0.33, 3.4),
    ],
)
def test_create_solid_solution_uniform(concentration, expected_min_distance):
    material = Material.create(BULK_HfO2)
    result = create_solid_solution(
        material,
        "Hf",
        "Zr",
        concentration,
        seed=42,
        site_selection_method="uniform",
        tolerance=0.001,
    )
    assert _min_nearest_neighbor_distance(result, "Zr") > expected_min_distance


def test_create_solid_solution_records_target_and_actual_concentration():
    material = Material.create(BULK_HfO2)
    target_concentration = 0.37
    result = create_solid_solution(
        material,
        "Hf",
        "Zr",
        target_concentration,
        seed=42,
        tolerance=0.01,
        site_selection_method="uniform",
    )
    build_step = result.metadata.get_build_metadata_of_type("SolidSolutionConfiguration")
    assert build_step is not None
    configuration = build_step.configuration
    assert configuration["target_concentration"] == target_concentration
    assert configuration["actual_concentration"] == pytest.approx(0.375)
    assert configuration["target_concentration"] != configuration["actual_concentration"]
