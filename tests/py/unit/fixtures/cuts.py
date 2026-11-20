FULL_MATERIAL = {
    "basis": {
        "constraints": [],
        "coordinates": [
            {"id": 0, "value": [0.0, 0.0, 0.0]},
            {"id": 1, "value": [0.0, 0.5, 0.5]},
            {"id": 2, "value": [0.5, 0.0, 0.5]},
            {"id": 3, "value": [0.5, 0.5, 0.0]},
        ],
        "elements": [
            {"id": 0, "value": "Ni"},
            {"id": 1, "value": "Ni"},
            {"id": 2, "value": "Ni"},
            {"id": 3, "value": "Ni"},
        ],
        "labels": [],
        "units": "crystal",
    },
    "consistencyChecks": None,
    "derivedProperties": None,
    "description": None,
    "descriptionObject": None,
    "external": None,
    "field_id": None,
    "formula": None,
    "icsdId": None,
    "isDefault": False,
    "isNonPeriodic": False,
    "lattice": {
        "a": 3.52,
        "alpha": 90.0,
        "b": 3.52,
        "beta": 90.0,
        "c": 3.52,
        "gamma": 90.0,
        "type": "TRI",
        "units": {"angle": "degree", "length": "angstrom"},
    },
    "metadata": {"boundaryConditions": {"offset": 0, "type": "pbc"}},
    "name": "",
    "scaledHash": None,
    "schemaVersion": "2022.8.16",
    "slug": None,
    "src": None,
    "systemName": None,
    "unitCellFormula": None,
}

CAVITY_MATERIAL_BASIS = {
    "basis": {
        "constraints": [],
        "coordinates": [
            {"id": 1, "value": [0.0, 0.5, 0.5]},
            {"id": 2, "value": [0.5, 0.0, 0.5]},
            {"id": 4, "value": [0.5, 0.5, 0.0]},
        ],
        "elements": [{"id": 1, "value": "Ni"}, {"id": 2, "value": "Ni"}, {"id": 4, "value": "Au"}],
        "labels": [],
        "units": "crystal",
    }
}


SECTION_MATERIAL_BASIS = {
    "basis": {
        "constraints": [],
        "coordinates": [{"id": 0, "value": [0.0, 0.0, 0.0]}, {"id": 3, "value": [0.5, 0.5, 0.0]}],
        "elements": [{"id": 0, "value": "Ni"}, {"id": 3, "value": "Ni"}],
        "labels": [],
        "units": "crystal",
    }
}

SECTION_MATERIAL_BASIS_EXTRA_ATOM = {
    "basis": {
        "constraints": [],
        "coordinates": [
            {"id": 0, "value": [0.0, 0.0, 0.0]},
            {"id": 3, "value": [0.5, 0.5, 0.0]},
            {"id": 4, "value": [0.51, 0.51, 0.0]},  # Extra atom collides with Au in cavity material
        ],
        "elements": [{"id": 0, "value": "Ni"}, {"id": 3, "value": "Ni"}, {"id": 4, "value": "O"}],
        "labels": [],
        "units": "crystal",
    }
}

MERGED_SECTION_CAVITY_BASIS = {
    "elements": [
        {"id": 0, "value": "Ni"},
        {"id": 1, "value": "Ni"},
        {"id": 2, "value": "Ni"},
        {"id": 4, "value": "Au"},
    ],
    "coordinates": [
        {"id": 0, "value": [0.0, 0.0, 0.0]},
        {"id": 1, "value": [0.0, 0.5, 0.5]},
        {"id": 2, "value": [0.5, 0.0, 0.5]},
        {"id": 4, "value": [0.5, 0.5, 0.0]},
    ],
    "labels": [],
}

MERGED_CAVITY_SECTION_BASIS = {
    "elements": [
        {"id": 1, "value": "Ni"},
        {"id": 2, "value": "Ni"},
        {"id": 0, "value": "Ni"},
        {"id": 3, "value": "Ni"},
    ],
    "coordinates": [
        {"id": 1, "value": [0.0, 0.5, 0.5]},
        {"id": 2, "value": [0.5, 0.0, 0.5]},
        {"id": 0, "value": [0.0, 0.0, 0.0]},
        {"id": 3, "value": [0.5, 0.5, 0.0]},
    ],
    "labels": [],
}
