"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@mat3ra/utils");
const constants_1 = require("../constants");
const lattice_1 = require("../lattice/lattice");
/**
 * Scales one lattice vector for the given material
 * @param material {Material} The material acted upon.
 * @param key {String} Lattice vector key.
 * @param factor {Number} Float scaling factor.
 */
function scaleOneLatticeVector(material, key = "a", factor = 1.0) {
    const lattice = { ...material.lattice };
    if (lattice.vectors === undefined) {
        throw new Error("Lattice vectors are undefined");
    }
    lattice.vectors[key] = lattice.vectors[key].map((v) => v * factor);
    material.lattice = lattice_1.Lattice.fromVectors(lattice.vectors).toJSON();
}
/**
 * Updates the size of a materials lattice using the minimumLatticeSize function.
 * The new size of the material is calculated based on the materials basis.
 * @param material {Material}
 */
function scaleLatticeToMakeNonPeriodic(material) {
    material.lattice = lattice_1.Lattice.fromConfigPartial({
        a: material.Basis.getMinimumLatticeSize(),
        type: "CUB",
    }).toJSON();
}
/**
 * Updates the basis of a material by translating the coordinates
 * so that the center of the material and lattice are aligned.
 * @param material {Material}
 * */
function translateAtomsToCenter(material) {
    const originalUnits = material.Basis.units;
    material.toCartesian();
    const updatedBasis = material.Basis;
    const centerOfCoordinates = updatedBasis.centerOfCoordinatesPoint;
    const centerOfLattice = utils_1.Utils.math.multiply(0.5, material.Lattice.vectorArrays.reduce((a, b) => utils_1.Utils.math.add(a, b)));
    const translationVector = utils_1.Utils.math.subtract(centerOfLattice, centerOfCoordinates);
    updatedBasis.translateByVector(translationVector);
    material.setBasis(updatedBasis.toJSON());
    if (originalUnits !== constants_1.ATOMIC_COORD_UNITS.cartesian)
        material.toCrystal();
}
exports.default = {
    scaleOneLatticeVector,
    scaleLatticeToMakeNonPeriodic,
    translateAtomsToCenter,
};
