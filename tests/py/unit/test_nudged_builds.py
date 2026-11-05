import copy
from functools import partialmethod

import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.helpers import create_defect_point_interstitial, create_interface_zsl, create_slab
from mat3ra.made.tools.third_party import PymatgenSlabGenerator, PymatgenStructure
from unit.fixtures.bulk import BULK_Hf2O_MCL, BULK_Ni_PRIMITIVE, BULK_Si_PRIMITIVE
from unit.fixtures.monolayer import GRAPHENE

# Another runtime computes the same values within 1-2 units in the last place (ulp), e.g. pymatgen's oriented unit
# cell in Pyodide; an origin shift by a lattice vector is the same crystal.
ULP_STEPS = [-2, -1, 0, 1, 2]
ORIGIN_SHIFT = [1, -1, 1]
SLAB_GENERATOR_INIT = PymatgenSlabGenerator.__init__

SLAB_PARAMETERS = {"miller_indices": (0, 0, 1), "number_of_layers": 3, "vacuum": 0}
INTERFACE_PARAMETERS = {
    "substrate_miller_indices": (1, 1, 1),
    "substrate_number_of_layers": 3,
    "gap": 3.0,
    "max_area": 90,
    "max_area_ratio_tol": 0.09,
    "max_length_tol": 0.05,
    "max_angle_tol": 0.02,
}
INTERSTITIAL_PARAMETERS = {"coordinate": [0.25, 0.25, 0.5], "element": "Ge", "placement_method": "voronoi_site"}


def nudge(values, steps):
    for _ in range(abs(steps)):
        values = np.nextafter(values, np.sign(steps) * np.inf)
    return values


def get_material_with_nudged_coordinates(material_config, steps):
    nudged_config = copy.deepcopy(material_config)
    for coordinate in nudged_config["basis"]["coordinates"]:
        coordinate["value"] = nudge(np.array(coordinate["value"]), steps).tolist()
    return Material.create(nudged_config)


def get_material_with_shifted_origin(material_config):
    shifted_config = copy.deepcopy(material_config)
    for coordinate in shifted_config["basis"]["coordinates"]:
        coordinate["value"] = (np.array(coordinate["value"]) + ORIGIN_SHIFT).tolist()
    return Material.create(shifted_config)


def init_with_nudged_oriented_unit_cell(generator, *args, steps=0, **kwargs):
    SLAB_GENERATOR_INIT(generator, *args, **kwargs)
    oriented_unit_cell = generator.oriented_unit_cell
    generator.oriented_unit_cell = PymatgenStructure(
        oriented_unit_cell.lattice,
        oriented_unit_cell.species,
        nudge(oriented_unit_cell.frac_coords, steps),
        site_properties=oriented_unit_cell.site_properties,
    )


def build(builder, material_config, steps, parameters):
    return [
        builder(get_material_with_nudged_coordinates(material_config, steps), **parameters),
        builder(get_material_with_shifted_origin(material_config), **parameters),
    ]


def get_stored_form(material):
    basis = material.basis.clone()
    basis.to_standard_representation()
    return basis.to_dict(), material.lattice.to_dict(), material.hash


def create_interface_on_substrate(film, **parameters):
    return create_interface_zsl(Material.create(BULK_Ni_PRIMITIVE), film, **parameters)


@pytest.mark.parametrize(
    "builder, material_config, parameters, expected_hash",
    [
        # The cut of monoclinic HfO2 (001) fell on the cell boundary: 17 layers natively, 16 in Pyodide.
        (create_slab, BULK_Hf2O_MCL, SLAB_PARAMETERS, "28e7d4d495308e68076eb118b6d26cbb"),
        (create_interface_on_substrate, GRAPHENE, INTERFACE_PARAMETERS, "e1af20b86cde077ba9ce1af983805372"),
        (
            create_defect_point_interstitial,
            BULK_Si_PRIMITIVE,
            INTERSTITIAL_PARAMETERS,
            "d147560ab2bcc45c196a82ea967131f0",
        ),
    ],
)
@pytest.mark.parametrize("steps", ULP_STEPS)
def test_build_from_nudged_input(builder, material_config, parameters, expected_hash, steps, monkeypatch):
    monkeypatch.setattr(
        PymatgenSlabGenerator, "__init__", partialmethod(init_with_nudged_oriented_unit_cell, steps=steps)
    )
    stored_forms = [get_stored_form(material) for material in build(builder, material_config, steps, parameters)]
    assert stored_forms[0] == stored_forms[1]
    assert stored_forms[0][2] == expected_hash
