"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.atomsCount = atomsCount;
const math_1 = require("@mat3ra/code/dist/js/math");
const utils_1 = require("@mat3ra/utils");
const underscore_string_1 = __importDefault(require("underscore.string"));
const constrained_basis_1 = require("../basis/constrained_basis");
const cell_1 = require("../cell/cell");
const constants_1 = require("../constants");
const lattice_1 = require("../lattice/lattice");
const _print = (x, printFormat = "%14.9f") => underscore_string_1.default.sprintf(printFormat, math_1.math.precise(x));
const _latticeVectorsToString = (vectors) => vectors.map((v) => v.map((c) => _print(c)).join("\t")).join("\n");
const atomicConstraintsCharFromBool = (bool) => (bool ? "T" : "F");
/**
 * Obtain a textual representation of a material in POSCAR format.
 * @param materialOrConfig - material class instance or config object.
 * @param omitConstraints - whether to discard constraints passed with material.
 */
function toPoscar(materialOrConfig, omitConstraints = false) {
    const lattice = new lattice_1.Lattice(materialOrConfig.lattice);
    const vectorsAsString = _latticeVectorsToString(lattice.vectorArrays);
    // @ts-ignore
    const basis = new constrained_basis_1.ConstrainedBasis({
        ...materialOrConfig.basis,
        cell: cell_1.Cell.fromVectorsArray(lattice.vectorArrays),
    });
    const BasisLines = [];
    let addSelectiveDynamics = false;
    basis._elements.values.forEach((item, idx) => {
        const coord = basis.getCoordinateValueByIndex(idx).map((x) => _print(x));
        const constraintsAsString = omitConstraints
            ? ""
            : basis.AtomicConstraints.getAsStringByIndex(idx, atomicConstraintsCharFromBool);
        if (constraintsAsString && !omitConstraints)
            addSelectiveDynamics = true;
        BasisLines.push([coord.join(" "), constraintsAsString, item].join(" "));
    });
    const basisContent = BasisLines.join("\n");
    const elementsLine = basis.elementCounts.map((e) => e.value).join(" ");
    const countsLine = basis.elementCounts.map((e) => parseInt(`${e.count}`, 10)).join(" ");
    const coordsType = materialOrConfig.basis.units === constants_1.ATOMIC_COORD_UNITS.cartesian ? "cartesian" : "direct";
    return [
        materialOrConfig.name,
        "1.0",
        vectorsAsString,
        elementsLine,
        countsLine,
        // add selective dynamics only if there are some constraints!
        ...(addSelectiveDynamics ? ["Selective dynamics"] : []),
        coordsType,
        basisContent,
    ].join("\n");
}
/**
 * @summary calculates the number of atoms in a poscar file based on the summation of the numbers in line 7 of the file.
 * Poscar file formatting: https://www.vasp.at/wiki/index.php/POSCAR
 */
function atomsCount(poscarFileContent) {
    const lines = utils_1.Utils.str.removeCommentsFromSourceCode(poscarFileContent).split("\n");
    const atomsLine = lines[6].split(/\s+/);
    return atomsLine.map((x) => parseInt(x, 10)).reduce((a, b) => a + b);
}
/**
 * Parses POSCAR file into a Material config object.
 * @param fileContent - POSCAR file content.
 * @return Material config.
 */
function fromPoscar(fileContent) {
    const cleanContent = utils_1.Utils.str.removeCommentsFromSourceCode(fileContent, "fortran");
    const lines = cleanContent.split("\n");
    const comment = lines[0];
    // TODO: alat should be handled!!!!
    // const latticeConstant = parseFloat(lines[1].trim());
    // Atom symbols and counts
    const atomSymbols = lines[5].trim().split(/\s+/);
    const atomCounts = lines[6].trim().split(/\s+/).map(Number);
    // Check if selective dynamics and coordinates type is used
    let selectiveDynamics = false;
    let coordinateType = "";
    let startLine = 7;
    if (lines[startLine].trim()[0].toLowerCase() === "s") {
        selectiveDynamics = true;
        coordinateType = lines[8].trim()[0].toLowerCase();
        startLine = 9;
    }
    else {
        coordinateType = lines[7].trim()[0].toLowerCase();
        startLine = 8;
    }
    const elements = atomSymbols
        .map((symbol, i) => Array(atomCounts[i]).fill(symbol))
        .reduce((a, b) => a.concat(b), []);
    // Atom coordinates and constraints
    const coordinates = [];
    const constraints = [];
    let atomIndex = 0;
    for (let i = 0; i < atomSymbols.length; i++) {
        for (let j = 0; j < atomCounts[i]; j++) {
            const lineComponents = lines[startLine + atomIndex].trim().split(/\s+/);
            const coordinate = [
                parseFloat(lineComponents[0]),
                parseFloat(lineComponents[1]),
                parseFloat(lineComponents[2]),
            ];
            coordinates.push(coordinate);
            // Add constraints if selective dynamics is used
            if (selectiveDynamics) {
                const constraint = [
                    lineComponents[3] === "T",
                    lineComponents[4] === "T",
                    lineComponents[5] === "T",
                ];
                constraints.push(constraint);
            }
            atomIndex += 1;
        }
    }
    const lattice = lattice_1.Lattice.fromVectorsArray([
        lines[2].trim().split(/\s+/).map(Number),
        lines[3].trim().split(/\s+/).map(Number),
        lines[4].trim().split(/\s+/).map(Number),
    ]);
    const basis = constrained_basis_1.ConstrainedBasis.fromElementsCoordinatesAndConstraints({
        elements,
        coordinates,
        units: coordinateType === "c"
            ? constants_1.ATOMIC_COORD_UNITS.cartesian
            : constants_1.ATOMIC_COORD_UNITS.crystal,
        cell: cell_1.Cell.fromVectorsArray(lattice.vectorArrays),
        constraints,
    });
    const materialConfig = {
        lattice: lattice.toJSON(),
        basis: basis.toJSON(),
        name: comment,
        isNonPeriodic: false,
    };
    return materialConfig;
}
/**
 * @summary Checks if a string has a POSCAR format (first 8 lines are read)
 * @param text - string to check
 */
function isPoscar(text) {
    const lines = utils_1.Utils.str.removeCommentsFromSourceCode(text, "fortran").split("\n");
    // Checking number of lines, minimum requirement for POSCAR
    if (lines.length < 7) {
        return false;
    }
    // Check the lattice constant (a single floating point number)
    if (!/^[+-]?[\d.]+$/.test(lines[1].trim())) {
        return false;
    }
    // Check the lattice vectors (three lines, each with three floating point numbers)
    for (let i = 2; i <= 4; i++) {
        if (!/^[-+]?\d*\.\d+\s+[-+]?\d*\.\d+\s+[-+]?\d*\.\d+$/.test(lines[i].trim())) {
            return false;
        }
    }
    // Check the atomic species line (alphabetic characters, space-separated)
    if (!/^[a-zA-Z\s]+$/.test(lines[5].trim())) {
        return false;
    }
    // Check the number of atoms per species line (digits, space-separated)
    if (!/^[\d\s]+$/.test(lines[6].trim())) {
        return false;
    }
    // Check the coordinate type line (only first character is neccessary, "s" or "S" for "Selective dynamics",
    // "d" or "D" for "Direct", or "c" or "C" for "Cartesian")
    if (!/^[sdc]/.test(lines[7].trim().toLowerCase())) {
        return false;
    }
    return true;
}
exports.default = {
    isPoscar,
    toPoscar,
    fromPoscar,
    atomicConstraintsCharFromBool,
    atomsCount,
};
