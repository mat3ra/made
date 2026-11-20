from unit.utils import OSPlatform

VACANCY_DEFECT_BULK_PRIMITIVE_Si = {
    "name": "Silicon FCC with vacancy defect",
    "lattice": {
        "a": 3.867,
        "b": 3.867,
        "c": 3.867,
        "alpha": 60.0,
        "beta": 60.0,
        "gamma": 60.0,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "FCC",
    },
    "basis": {
        "elements": [{"id": 0, "value": "Si"}],
        "coordinates": [{"id": 0, "value": [0.25, 0.25, 0.25]}],
        "units": "crystal",
        "labels": [],
        "constraints": [],
    },
}

SUBSTITUTION_DEFECT_BULK_PRIMITIVE_Si = {
    "name": "Silicon FCC with substitutional defect",
    "lattice": {
        "a": 3.867,
        "b": 3.867,
        "c": 3.867,
        "alpha": 60.0,
        "beta": 60.0,
        "gamma": 60.0,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "FCC",
    },
    "basis": {
        "elements": [{"id": 0, "value": "Si"}, {"id": 1, "value": "Ge"}],
        "coordinates": [{"id": 0, "value": [0.25, 0.25, 0.25]}, {"id": 1, "value": [0.0, 0.0, 0.0]}],
        "units": "crystal",
        "labels": [],
        "constraints": [],
    },
}

INTERSTITIAL_DEFECT_BULK_PRIMITIVE_Si = {
    "name": "Silicon FCC with interstitial defect",
    "lattice": {
        "a": 3.867,
        "b": 3.867,
        "c": 3.867,
        "alpha": 60.0,
        "beta": 60.0,
        "gamma": 60.0,
        "units": {"length": "angstrom", "angle": "degree"},
        "type": "FCC",
    },
    "basis": {
        "elements": [{"id": 0, "value": "Si"}, {"id": 1, "value": "Si"}, {"id": 2, "value": "C"}],
        "coordinates": [
            {"id": 0, "value": [0.0, 0.0, 0.0]},
            {"id": 1, "value": [0.25, 0.25, 0.25]},
            {"id": 2, "value": [0.5, 0.5, 0.5]},
        ],
        "units": "crystal",
        "labels": [],
        "constraints": [],
    },
}

INTERSTITIAL_VORONOI_DEFECT_BULK_PRIMITIVE_Si = {
    OSPlatform.DARWIN: {
        "name": "Silicon FCC with interstitial defect",
        "basis": {
            "elements": [{"id": 0, "value": "Si"}, {"id": 1, "value": "Si"}, {"id": 2, "value": "Ge"}],
            "coordinates": [
                {"id": 0, "value": [0.0, 0.0, 0.0]},
                {"id": 1, "value": [0.25, 0.25, 0.25]},
                {"id": 2, "value": [0.625, 0.625, 0.125]},
            ],
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
            "type": "FCC",
        },
    },
    OSPlatform.OTHER: {
        "name": "Silicon FCC with interstitial defect",
        "basis": {
            "elements": [{"id": 0, "value": "Si"}, {"id": 1, "value": "Si"}, {"id": 2, "value": "Ge"}],
            "coordinates": [
                {"id": 0, "value": [0.0, 0.0, 0.0]},
                {"id": 1, "value": [0.25, 0.25, 0.25]},
                {"id": 2, "value": [0.5, 0.5, 0.5]},
            ],
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
            "type": "FCC",
        },
    },
}

MULTIPLE_POINT_DEFECTS_BULK_Si_CONVENTIONAL = {
    "name": "Si8 with vacancy defect with interstitial defect with substitutional defect",
    "basis": {
        "elements": [
            {"id": 0, "value": "Si"},
            {"id": 1, "value": "Si"},
            {"id": 2, "value": "Si"},
            {"id": 3, "value": "Si"},
            {"id": 4, "value": "Si"},
            {"id": 5, "value": "Si"},
            {"id": 6, "value": "N"},
            {"id": 7, "value": "Ge"},
        ],
        "coordinates": [
            {"id": 0, "value": [0.5, 0.0, 0.0]},
            {"id": 1, "value": [0.25, 0.25, 0.75]},
            {"id": 2, "value": [0.25, 0.75, 0.25]},
            {"id": 3, "value": [0.0, 0.0, 0.5]},
            {"id": 4, "value": [0.75, 0.25, 0.25]},
            {"id": 5, "value": [0.0, 0.5, 0.0]},
            {"id": 6, "value": [0.25, 0.25, 0.25]},
            {"id": 7, "value": [0.5, 0.5, 0.5]},
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
