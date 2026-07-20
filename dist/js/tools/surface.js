"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@mat3ra/utils");
const lattice_1 = require("../lattice/lattice");
const supercell_1 = __importDefault(require("./supercell"));
const MULT = utils_1.Utils.math.multiply;
const ADD = utils_1.Utils.math.add;
const DOT = utils_1.Utils.math.product;
const getMatrixInLeftHandedRepresentation = (matrix) => {
    return utils_1.Utils.math.det(matrix) < 0 ? MULT(matrix, -1) : matrix;
};
/**
 * Helper function for extended GCD.
 * Inspired by https://gitlab.com/ase/ase/-/blob/20401e2596821a85f17ced1cb18f32c508e35fb0/ase/build/general_surface.py
 * @param {Number} a
 * @param {Number} b
 * @return {Array}
 */
function extGCD(a, b) {
    if (b === 0)
        return [1, 0];
    if (utils_1.Utils.math.mod(a, b) === 0)
        return [0, 1];
    const [x, y] = extGCD(b, utils_1.Utils.math.mod(a, b));
    return [y, x - y * utils_1.Utils.math.floor(a / b)];
}
/**
 * Generates a slab scaling matrix for the specified cell based on miller indices.
 * Inspired by from https://gitlab.com/ase/ase/blob/master/ase/build/general_surface.py.
 * @param cell {Cell}
 * @param millerIndices {Number[]}
 * @param tol {Number} Zero-value tolerance
 * @return {Number[][]}
 */
function getMillerScalingMatrix(cell, millerIndices, tol = 1e-8) {
    if (!millerIndices.reduce((a, b) => utils_1.Utils.math.abs(a) + utils_1.Utils.math.abs(b)))
        throw new Error("Miller indices are zeros.");
    let scalingMatrix;
    const [h, k, l] = millerIndices;
    const [h0, k0, l0] = millerIndices.map((i) => i === 0);
    if ((h0 && k0) || (h0 && l0) || (k0 && l0)) {
        // if any two indices are zero
        if (!h0) {
            scalingMatrix = [
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 0],
            ];
        }
        if (!k0) {
            scalingMatrix = [
                [0, 0, 1],
                [1, 0, 0],
                [0, 1, 0],
            ];
        }
        if (!l0) {
            scalingMatrix = [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1],
            ];
        }
    }
    else {
        const [a1, a2, a3] = cell.vectorArrays;
        // z1 = (k * a1 - h * a2)
        // z2 = (l * a1 - h * a3)
        // z3 = l * a2 - k * a3)
        const z1 = ADD(MULT(k, a1), -MULT(h, a2));
        const z2 = ADD(MULT(l, a1), -MULT(h, a3));
        const z3 = ADD(MULT(l, a2), -MULT(k, a3));
        let [p, q] = extGCD(k, l);
        // @ts-ignore
        const k1 = DOT(ADD(MULT(p, z1), MULT(q, z2)), z3);
        // @ts-ignore
        const k2 = DOT(ADD(MULT(l, z1), -MULT(k, z2)), z3);
        // @ts-ignore
        if (utils_1.Utils.math.abs(k2) > tol) {
            // For mathjs version 3.20: round(-0.5) = -0
            // For mathjs version 5.10: round(-0.5) = -1
            // Here we specify rounding method to Bankers
            // For Python 3.11: round(-0.5) = 0
            // @ts-ignore - mathjs v12 dot return type
            const value = k1 / k2;
            const roundedValue = utils_1.Utils.math.roundCustom(value, 0, utils_1.Utils.math.RoundingMethod.Bankers);
            const i = -roundedValue;
            [p, q] = [p + i * l, q - i * k];
        }
        const [a, b] = extGCD(p * k + q * l, h);
        const c1 = [p * k + q * l, -p * h, -q * h];
        const c2 = [0, l, -k].map((c) => utils_1.Utils.math.trunc(c / utils_1.Utils.math.gcd(l, k))); // floor division
        const c3 = [b, a * p, a * q];
        scalingMatrix = [c1, c2, c3];
    }
    // @ts-ignore
    return getMatrixInLeftHandedRepresentation(scalingMatrix);
}
/**
 * Scale the surface cell in out-of-plane direction according to thickness
 *  and construct the lateral supercell from vx/vy parameters.
 * @param bulkCell {Cell}
 * @param surfaceCell {Cell}
 * @param outOfPlaneAxisIndex {Number} Index of the cell vector most collinear with the out-of-surface-plane vector
 * @param thickness {Number} Surface (Slab) thickness in layers (Positive Integer).
 * @param vx {Number} Size of lateral supercell along the direction of the first (x) cell vector (Positive Integer).
 * @param vy {Number} Size of lateral supercell along the direction of the second (y) cell vector (Positive Integer).
 * @return {Number[][]}
 */
function getDimensionsScalingMatrix(outOfPlaneAxisIndex, thickness, vx, vy) {
    const transformationMatrix = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ];
    const vxIndex = outOfPlaneAxisIndex === 2 ? 0 : outOfPlaneAxisIndex + 1;
    const vyIndex = vxIndex === 2 ? 0 : vxIndex + 1;
    transformationMatrix[outOfPlaneAxisIndex] = MULT(thickness, transformationMatrix[outOfPlaneAxisIndex]);
    transformationMatrix[vxIndex] = MULT(vx, transformationMatrix[vxIndex]);
    transformationMatrix[vyIndex] = MULT(vy, transformationMatrix[vyIndex]);
    return transformationMatrix;
}
/*
 * Generate a config object for a surface based on a set of parameters.
 * @param material {Material} The parent material (bulk) this surface is constructed from
 * @param millerIndices {Number[]} Miller Indices that define the surface cleavage.
 * @param numberOfLayers {Number} Surface (Slab) thickness in layers (Positive Integer).
 * @param vx {Number} Size of lateral supercell along the direction of the first (x) cell vector (Positive Integer).
 * @param vy {Number} Size of lateral supercell along the direction of the second (y) cell vector (Positive Integer).
 * @return {Object}
 */
function generateConfig(material, millerIndices, numberOfLayers = 1, vx = 1, vy = 1) {
    if (numberOfLayers < 1)
        throw new Error("Made.tools.surface.generateConfig: number of layers < 1.");
    const cell = material.getLattice().vectors;
    const millerScalingMatrix = getMillerScalingMatrix(cell, millerIndices);
    const millerSupercell = cell.cloneAndScaleByMatrix(millerScalingMatrix);
    const millerPlanePseudoNormal = cell.convertPointToCartesian(millerIndices);
    const outOfPlaneAxisIndex = millerSupercell.getMostCollinearVectorIndex(millerPlanePseudoNormal);
    const dimensionsScalingMatrix = getDimensionsScalingMatrix(outOfPlaneAxisIndex, numberOfLayers, vx, vy);
    const supercellMatrix = MULT(dimensionsScalingMatrix, millerScalingMatrix);
    const supercell = millerSupercell.cloneAndScaleByMatrix(dimensionsScalingMatrix);
    const tempBasis = material.getBasis().clone();
    const newBasis = supercell_1.default.generateNewBasisWithinSupercell(tempBasis, cell, supercell, supercellMatrix);
    const newLattice = lattice_1.Lattice.fromVectors({
        a: supercell.vectorArrays[0],
        b: supercell.vectorArrays[1],
        c: supercell.vectorArrays[2],
    });
    return {
        name: `${material.name} - slab ${JSON.stringify(millerIndices)}`,
        basis: newBasis.toJSON(),
        lattice: newLattice.toJSON(),
        // extra parameter for use in creating vacuum etc.
        outOfPlaneAxisIndex,
        metadata: {},
    };
}
exports.default = {
    generateConfig,
};
