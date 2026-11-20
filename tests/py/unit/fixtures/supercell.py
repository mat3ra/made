from typing import Any, Dict

SI_SUPERCELL_FLIPPED_Z: Dict[str, Any] = {
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
        "type": "TRI",
        "units": {"angle": "degree", "length": "angstrom"},
    },
    "isNonPeriodic": False,
}

SI_SUPERCELL_2X2X1: Dict[str, Any] = {
    "name": "Silicon FCC",
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
            {"id": 0, "value": [0.0, 0.0, 0.0]},
            {"id": 1, "value": [0.125, 0.125, 0.25]},
            {"id": 2, "value": [0.0, 0.5, 0.0]},
            {"id": 3, "value": [0.125, 0.625, 0.25]},
            {"id": 4, "value": [0.5, 0.0, 0.0]},
            {"id": 5, "value": [0.625, 0.125, 0.25]},
            {"id": 6, "value": [0.5, 0.5, 0.0]},
            {"id": 7, "value": [0.625, 0.625, 0.25]},
        ],
        "units": "crystal",
        "constraints": [],
        "labels": [],
    },
    "lattice": {
        "a": 7.734,
        "b": 7.734,
        "c": 3.867,
        "alpha": 60.0,
        "beta": 60.0,
        "gamma": 60.0,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "TRI",
    },
    "isNonPeriodic": False,
    "metadata": {"boundaryConditions": {"type": "pbc", "offset": 0}},
}
