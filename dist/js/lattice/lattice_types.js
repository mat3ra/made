"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LATTICE_TYPE_CONFIGS = exports.DEFAULT_LATTICE_UNITS = exports.LatticeTypeExtended = void 0;
var LatticeTypeExtended;
(function (LatticeTypeExtended) {
    LatticeTypeExtended["BCC"] = "BCC";
    LatticeTypeExtended["BCT_1"] = "BCT-1";
    LatticeTypeExtended["BCT_2"] = "BCT-2";
    LatticeTypeExtended["CUB"] = "CUB";
    LatticeTypeExtended["FCC"] = "FCC";
    LatticeTypeExtended["HEX"] = "HEX";
    LatticeTypeExtended["MCL"] = "MCL";
    LatticeTypeExtended["MCLC_1"] = "MCLC-1";
    LatticeTypeExtended["MCLC_2"] = "MCLC-2";
    LatticeTypeExtended["MCLC_3"] = "MCLC-3";
    LatticeTypeExtended["MCLC_4"] = "MCLC-4";
    LatticeTypeExtended["MCLC_5"] = "MCLC-5";
    LatticeTypeExtended["ORC"] = "ORC";
    LatticeTypeExtended["ORCC"] = "ORCC";
    LatticeTypeExtended["ORCF_1"] = "ORCF-1";
    LatticeTypeExtended["ORCF_2"] = "ORCF-2";
    LatticeTypeExtended["ORCF_3"] = "ORCF-3";
    LatticeTypeExtended["ORCI"] = "ORCI";
    LatticeTypeExtended["RHL_1"] = "RHL-1";
    LatticeTypeExtended["RHL_2"] = "RHL-2";
    LatticeTypeExtended["TET"] = "TET";
    LatticeTypeExtended["TRI_1a"] = "TRI_1a";
    LatticeTypeExtended["TRI_2a"] = "TRI_2a";
    LatticeTypeExtended["TRI_1b"] = "TRI_1b";
})(LatticeTypeExtended || (exports.LatticeTypeExtended = LatticeTypeExtended = {}));
exports.DEFAULT_LATTICE_UNITS = {
    // by default lattice vectors shall be measured in angstrom, angles - in degrees
    length: {
        angstrom: "angstrom",
    },
    angle: {
        degree: "degree",
    },
};
exports.LATTICE_TYPE_CONFIGS = [
    {
        label: "Simple Cubic",
        code: "CUB",
        // editables for primitive cell => WARNING: not tested
        editables: ["a"],
        // editables for conventional cell, taken from the publication above
        editablesConventional: ["a"],
    },
    {
        label: "Face-centered Cubic",
        code: "FCC",
        editables: ["a"],
        editablesConventional: ["a"],
    },
    {
        label: "Body-centered Cubic",
        code: "BCC",
        editables: ["a"],
        editablesConventional: ["a"],
    },
    {
        label: "Tetragonal",
        code: "TET",
        editables: ["a", "c"],
        editablesConventional: ["a", "c"],
    },
    {
        label: "Body-centered Tetragonal",
        code: "BCT",
        editables: ["a"],
        editablesConventional: ["a", "c"],
    },
    {
        label: "Orthorombic",
        code: "ORC",
        editables: ["a", "b", "c"],
        editablesConventional: ["a", "b", "c"],
    },
    {
        label: "Orthorombic Face-centered",
        code: "ORCF",
        editables: ["a", "b", "c"],
        editablesConventional: ["a", "b", "c"],
    },
    {
        label: "Orthorombic Body-centered",
        code: "ORCI",
        editables: ["a", "alpha", "gamma"],
        editablesConventional: ["a", "b", "c"],
    },
    {
        label: "Orthorombic Base-centered",
        code: "ORCC",
        editables: ["a", "c", "alpha"],
        editablesConventional: ["a", "b", "c"],
    },
    {
        label: "Hexagonal",
        code: "HEX",
        editables: ["a", "c"],
        editablesConventional: ["a", "c"],
    },
    {
        label: "Rhombohedral",
        code: "RHL",
        editables: ["a", "alpha"],
        editablesConventional: ["a", "alpha"],
    },
    {
        label: "Monoclinic",
        code: "MCL",
        editables: ["a", "b", "c", "alpha"],
        editablesConventional: ["a", "b", "c", "alpha"],
    },
    {
        label: "Monoclinic Base-centered",
        code: "MCLC",
        editables: ["a", "c", "alpha", "gamma"],
        editablesConventional: ["a", "b", "c", "alpha"],
    },
    {
        label: "Triclinic",
        code: "TRI",
        editables: ["a", "b", "c", "alpha", "beta", "gamma"],
        editablesConventional: ["a", "b", "c", "alpha", "beta", "gamma"],
    },
];
