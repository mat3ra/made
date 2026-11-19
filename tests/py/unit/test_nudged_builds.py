import copy
import hashlib
import json
from functools import partialmethod

import numpy as np
import pytest
from mat3ra.made.material import Material
from mat3ra.made.tools.helpers import create_defect_point_interstitial, create_interface_zsl, create_slab
from mat3ra.made.tools.third_party import PymatgenSlabGenerator, PymatgenStructure
from unit.fixtures.bulk import BULK_Hf2O_MCL, BULK_Ni_PRIMITIVE, BULK_Si_PRIMITIVE
from unit.fixtures.monolayer import GRAPHENE

# Another runtime computes pymatgen's oriented unit cell within 1-2 units in the last place (ulp), as Pyodide does;
# an origin shift by a lattice vector stores the same structure.
ULP_STEPS = [-2, -1, 1, 2]
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
    """Moves each value by the given number of ulp."""
    for _ in range(abs(steps)):
        values = np.nextafter(values, np.sign(steps) * np.inf)
    return values


def get_material_with_shifted_origin(material_config):
    """The material with every coordinate shifted by a lattice vector."""
    shifted_config = copy.deepcopy(material_config)
    for coordinate in shifted_config["basis"]["coordinates"]:
        coordinate["value"] = (np.array(coordinate["value"]) + ORIGIN_SHIFT).tolist()
    return Material.create(shifted_config)


def init_with_nudged_oriented_unit_cell(generator, *args, steps=0, **kwargs):
    """SlabGenerator.__init__, then the oriented unit cell's fractional coordinates moved by the given number of ulp."""
    SLAB_GENERATOR_INIT(generator, *args, **kwargs)
    oriented_unit_cell = generator.oriented_unit_cell
    generator.oriented_unit_cell = PymatgenStructure(
        oriented_unit_cell.lattice,
        oriented_unit_cell.species,
        nudge(oriented_unit_cell.frac_coords, steps),
        site_properties=oriented_unit_cell.site_properties,
    )


def get_stored_form(material):
    """The material's basis in the standard representation and its lattice, as JSON at full precision."""
    basis = material.basis.clone()
    basis.to_standard_representation()
    return json.dumps([basis.to_dict(), material.lattice.to_dict()], sort_keys=True)


def create_interface_on_substrate(film, **parameters):
    """The ZSL interface of the film on Ni(111)."""
    return create_interface_zsl(Material.create(BULK_Ni_PRIMITIVE), film, **parameters)


@pytest.mark.parametrize(
    "builder, material_config, parameters, expected_digest",
    [
        # The cut of monoclinic HfO2 (001) fell on the cell boundary: 17 layers natively, 16 in Pyodide.
        (create_slab, BULK_Hf2O_MCL, SLAB_PARAMETERS, "c70def306899ad6db4f2e5ecac0242d9"),
        (create_interface_on_substrate, GRAPHENE, INTERFACE_PARAMETERS, "ec51be25bafb9878cdec7b8bb55d7816"),
    ],
)
@pytest.mark.parametrize("steps", ULP_STEPS)
def test_build_with_nudged_oriented_unit_cell(
    builder, material_config, parameters, expected_digest, steps, monkeypatch
):
    stored_form = get_stored_form(builder(Material.create(material_config), **parameters))
    monkeypatch.setattr(
        PymatgenSlabGenerator, "__init__", partialmethod(init_with_nudged_oriented_unit_cell, steps=steps)
    )
    assert get_stored_form(builder(get_material_with_shifted_origin(material_config), **parameters)) == stored_form
    assert hashlib.md5(stored_form.encode()).hexdigest() == expected_digest


@pytest.mark.parametrize(
    "builder, material_config, parameters, expected_digest",
    [
        (
            create_defect_point_interstitial,
            BULK_Si_PRIMITIVE,
            INTERSTITIAL_PARAMETERS,
            "46eb92e4ae20a5eb5baa04044bfe6b0f",
        ),
    ],
)
def test_build_with_shifted_origin(builder, material_config, parameters, expected_digest):
    stored_form = get_stored_form(builder(Material.create(material_config), **parameters))
    assert get_stored_form(builder(get_material_with_shifted_origin(material_config), **parameters)) == stored_form
    assert hashlib.md5(stored_form.encode()).hexdigest() == expected_digest
