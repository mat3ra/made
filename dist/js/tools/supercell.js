"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@mat3ra/utils");
const lattice_1 = require("../lattice/lattice");
const cell_1 = __importDefault(require("./cell"));
const ADD = utils_1.Utils.math.add;
/**
 * @summary Generates new basis for a supercell. For each site from basis generates shifts that are within supercell.
 */
function generateNewBasisWithinSupercell(basis, cell, supercell, supercellMatrix) {
    const oldBasis = basis.clone();
    const newBasis = basis.clone();
    newBasis.removeAllAtoms();
    oldBasis.toCrystal();
    newBasis.toCrystal();
    oldBasis.elements.forEach((element) => {
        const coordinate = oldBasis.getCoordinateValueById(element.id);
        const cartesianCoordinate = cell.convertPointToCartesian(coordinate);
        const shifts = cell_1.default.latticePointsInSupercell(supercellMatrix);
        shifts.forEach((combination) => {
            // "combination" is effectively a point in fractional coordinates here, hence the below
            const newPoint = ADD(cartesianCoordinate, supercell.convertPointToCartesian(combination));
            if (supercell.isPointInsideCell(newPoint)) {
                newBasis.addAtom({
                    element: element.value,
                    coordinate: supercell.convertPointToCrystal(newPoint),
                });
            }
        });
    });
    return newBasis;
}
/**
 * @summary Generates supercell config for the specified material.
 * @param material
 * @param supercellMatrix {Number[][]}
 */
function generateConfig(material, supercellMatrix) {
    const det = utils_1.Utils.math.det(supercellMatrix);
    if (det === 0) {
        throw new Error("Scaling matrix is degenerate.");
    }
    const cell = material.Lattice.vectors;
    const supercell = cell.cloneAndScaleByMatrix(supercellMatrix);
    const newBasis = generateNewBasisWithinSupercell(material.Basis, cell, supercell, supercellMatrix);
    const newLattice = lattice_1.Lattice.fromVectors({
        a: supercell.a,
        b: supercell.b,
        c: supercell.c,
    });
    return {
        name: `${material.name} - supercell ${JSON.stringify(supercellMatrix)}`,
        basis: newBasis.toJSON(),
        lattice: newLattice.toJSON(),
    };
}
exports.default = {
    generateConfig,
    generateNewBasisWithinSupercell,
};
