from typing import Final

BULK_Si_CONVENTIONAL_STRAINED: Final = {
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
        "a": 6.01564,
        "b": 6.01564,
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
