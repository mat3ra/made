from typing import Any, Dict

from mat3ra.standata.materials import Materials

BULK_SrTiO3 = Materials.get_by_name_first_match("SrTiO3")
BULK_GRAPHITE = Materials.get_by_name_first_match("Graphite")
BULK_SiO2 = Materials.get_by_name_first_match("SiO2")
BULK_Hf2O_MCL = Materials.get_by_name_first_match("Hafnium IV Oxide, MCL")
BULK_TiN = Materials.get_by_name_first_match("TiN")
BULK_Ni_PRIMITIVE = Materials.get_by_name_first_match("Nickel")
BULK_GRAPHENE = Materials.get_by_name_first_match("Graphene")

BULK_Si_PRIMITIVE: Dict[str, Any] = {
    "name": "Silicon FCC",
    "basis": {
        "constraints": [],
        "coordinates": [{"id": 0, "value": [0.0, 0.0, 0.0]}, {"id": 1, "value": [0.25, 0.25, 0.25]}],
        "elements": [{"id": 0, "value": "Si"}, {"id": 1, "value": "Si"}],
        "labels": [],
        "units": "crystal",
    },
    "lattice": {
        "a": 3.867,
        "alpha": 60.0,
        "b": 3.867,
        "beta": 60.0,
        "c": 3.867,
        "gamma": 60.0,
        "type": "FCC",
        "units": {"angle": "degree", "length": "angstrom"},
    },
}

BULK_Si_PRIMITIVIZED = {
    "metadata": {"build": [], "boundaryConditions": {"type": "pbc", "offset": 0}},
    "name": "Si2",
    "basis": {
        "elements": [{"id": 0, "value": "Si"}, {"id": 1, "value": "Si"}],
        "coordinates": [{"id": 0, "value": [0.5, 0.5, 0.5]}, {"id": 1, "value": [0.75, 0.75, 0.75]}],
        "units": "crystal",
        "labels": [],
        "constraints": [],
    },
    "lattice": {
        "a": 3.867,
        "b": 3.867,
        "c": 3.867,
        "alpha": 60.0,
        "beta": 60.0,
        "gamma": 60.0,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "TRI",
    },
}


BULK_Si_CONVENTIONAL: Dict[str, Any] = {
    "name": "Si8",
    "basis": {
        "elements": [
            {"id": 0, "value": "Si"},
            {"id": 1, "value": "Si"},
            {"id": 2, "value": "Si"},
            {"id": 3, "value": "Si"},
            {"id": 4, "value": "Si"},
            {"id": 5, "value": "Si"},
            {"id": 6, "value": "Si"},
            {"id": 7, "value": "Si"},
        ],
        "coordinates": [
            {"id": 0, "value": [0.5, 0.0, 0.0]},
            {"id": 1, "value": [0.25, 0.25, 0.75]},
            {"id": 2, "value": [0.5, 0.5, 0.5]},
            {"id": 3, "value": [0.25, 0.75, 0.25]},
            {"id": 4, "value": [0.0, 0.0, 0.5]},
            {"id": 5, "value": [0.75, 0.25, 0.25]},
            {"id": 6, "value": [0.0, 0.5, 0.0]},
            {"id": 7, "value": [0.75, 0.75, 0.75]},
        ],
        "units": "crystal",
        "constraints": [],
        "labels": [],
    },
    "lattice": {
        "a": 5.468763846,
        "b": 5.468763846,
        "c": 5.468763846,
        "alpha": 90.0,
        "beta": 90.0,
        "gamma": 90.0,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "TRI",
    },
    "isNonPeriodic": False,
    "metadata": {"boundaryConditions": {"type": "pbc", "offset": 0}},
}

BULK_Si_CONVENTIONAL_FILTERED: Dict[str, Any] = {
    "name": "Si",
    "basis": {
        "elements": [
            {"id": 0, "value": "Si"},
            {"id": 2, "value": "Si"},
        ],
        "coordinates": [
            {"id": 0, "value": [0.5, 0.0, 0.0]},
            {"id": 2, "value": [0.5, 0.5, 0.5]},
        ],
        "units": "crystal",
        "labels": [],
        "constraints": [],
    },
    "lattice": {
        "a": 5.468763846,
        "b": 5.468763846,
        "c": 5.468763846,
        "alpha": 90.0,
        "beta": 90.0,
        "gamma": 90.0,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "TRI",
    },
}

BULK_Ge_CONVENTIONAL: Dict[str, Any] = {
    "name": "Germanium FCC",
    "basis": {
        "units": "crystal",
        "elements": [
            {"id": 0, "value": "Ge"},
            {"id": 1, "value": "Ge"},
            {"id": 2, "value": "Ge"},
            {"id": 3, "value": "Ge"},
            {"id": 4, "value": "Ge"},
            {"id": 5, "value": "Ge"},
            {"id": 6, "value": "Ge"},
            {"id": 7, "value": "Ge"},
        ],
        "coordinates": [
            {"id": 0, "value": [0, 0, 0]},
            {"id": 1, "value": [0.5, 0.5, 0]},
            {"id": 2, "value": [0.5, 0, 0.5]},
            {"id": 3, "value": [0, 0.5, 0.5]},
            {"id": 4, "value": [0.25, 0.25, 0.25]},
            {"id": 5, "value": [0.75, 0.75, 0.25]},
            {"id": 6, "value": [0.75, 0.25, 0.75]},
            {"id": 7, "value": [0.25, 0.75, 0.75]},
        ],
        "constraints": [],
    },
    "lattice": {
        "a": 5.67099638511611,
        "b": 5.67099638511611,
        "c": 5.67099638511611,
        "alpha": 90,
        "beta": 90,
        "gamma": 90,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "CUB",
        "vectors": {"a": [5.671, 0, 0], "b": [0, 5.671, 0], "c": [0, 0, 5.671], "alat": 1, "units": "angstrom"},
    },
}
