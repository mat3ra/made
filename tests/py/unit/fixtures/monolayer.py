GRAPHENE = {
    "name": "Graphene",
    "basis": {
        "elements": [{"id": 0, "value": "C"}, {"id": 1, "value": "C"}],
        "coordinates": [{"id": 0, "value": [0, 0, 0]}, {"id": 1, "value": [0.333333, 0.666667, 0]}],
        "units": "crystal",
        "constraints": [],
    },
    "lattice": {
        "a": 2.467291,
        "b": 2.467291,
        "c": 20,
        "alpha": 90,
        "beta": 90,
        "gamma": 120,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "HEX",
    },
    "isNonPeriodic": False,
}

# TODO: Use material from Standata. Add materials equivalency comparator.
#  Right now generated Silicene monolayer and one from Standata differ in gamma angle (120 vs 60 degrees).
SILICENE = {
    "name": "Silicon FCC - Monolayer ((1, 1, 1))",
    "lattice": {
        "a": 3.8670001,
        "b": 3.8670001,
        "c": 11.3223581,
        "alpha": 90,
        "beta": 90,
        "gamma": 60,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "TRI",
    },
    "basis": {
        "elements": [{"id": 0, "value": "Si"}, {"id": 1, "value": "Si"}],
        "coordinates": [
            {"id": 0, "value": [0.916666311, 0.916666303, 0.069716872]},
            {"id": 1, "value": [0.249999661, 0.249999659, 0.0]},
        ],
        "units": "crystal",
        "labels": [],
        "constraints": [],
    },
}
