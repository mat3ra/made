"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getPrimitiveLatticeVectorsFromConfig = getPrimitiveLatticeVectorsFromConfig;
const utils_1 = require("@mat3ra/utils");
/**
 * Routines for calculating primitive cell vectors from conventional cell Bravais parameters.
 * Following Setyawan, W., & Curtarolo, S. (2010). doi:10.1016/j.commatsci.2010.05.010
 */
const PRIMITIVE_CELLS = {
    CUB: ({ a }) => {
        return [
            [a, 0, 0],
            [0, a, 0],
            [0, 0, a],
        ];
    },
    FCC: ({ a }) => {
        return [
            [0.0, a / 2, a / 2],
            [a / 2, 0.0, a / 2],
            [a / 2, a / 2, 0.0],
        ];
    },
    BCC: ({ a }) => {
        return [
            [-a / 2, a / 2, a / 2],
            [a / 2, -a / 2, a / 2],
            [a / 2, a / 2, -a / 2],
        ];
    },
    TET: ({ a, c }) => {
        return [
            [a, 0, 0],
            [0, a, 0],
            [0, 0, c],
        ];
    },
    BCT: ({ a, c }) => {
        return [
            [-a / 2, a / 2, c / 2],
            [a / 2, -a / 2, c / 2],
            [a / 2, a / 2, -c / 2],
        ];
    },
    ORC: ({ a, b, c }) => {
        return [
            [a, 0, 0],
            [0, b, 0],
            [0, 0, c],
        ];
    },
    ORCF: ({ a, b, c }) => {
        return [
            [0, b / 2, c / 2],
            [a / 2, 0, c / 2],
            [a / 2, b / 2, 0],
        ];
    },
    ORCI: ({ a, b, c }) => {
        return [
            [-a / 2, b / 2, c / 2],
            [a / 2, -b / 2, c / 2],
            [a / 2, b / 2, -c / 2],
        ];
    },
    ORCC: ({ a, b, c }) => {
        return [
            [a / 2, b / 2, 0],
            [-a / 2, b / 2, 0],
            [0, 0, c],
        ];
    },
    HEX: ({ a, c }) => {
        return [
            [a / 2, (-a * Number(utils_1.Utils.math.sqrt(3))) / 2, 0],
            [a / 2, (a * Number(utils_1.Utils.math.sqrt(3))) / 2, 0],
            [0, 0, c],
        ];
    },
    RHL: ({ a, alpha }) => {
        const cosAlpha = Number(utils_1.Utils.math.cos((alpha / 180) * Number(utils_1.Utils.math.PI)));
        const cosHalfAlpha = Number(utils_1.Utils.math.sqrt((1 / 2) * (1 + cosAlpha)));
        const sinHalfAlpha = Number(utils_1.Utils.math.sqrt((1 / 2) * (1 - cosAlpha)));
        return [
            [a * cosHalfAlpha, -a * sinHalfAlpha, 0.0],
            [a * cosHalfAlpha, a * sinHalfAlpha, 0.0],
            [
                (a * cosAlpha) / cosHalfAlpha,
                0.0,
                a *
                    Number(utils_1.Utils.math.sqrt(1 - (cosAlpha * cosAlpha) / (cosHalfAlpha * cosHalfAlpha))),
            ],
        ];
    },
    MCL: ({ a, b, c, alpha }) => {
        const cosAlpha = Number(utils_1.Utils.math.cos((alpha / 180) * Number(utils_1.Utils.math.PI)));
        return [
            [a, 0, 0],
            [0, b, 0],
            [0, c * cosAlpha, c * Number(utils_1.Utils.math.sqrt(1 - cosAlpha * cosAlpha))],
        ];
    },
    MCLC: ({ a, b, c, alpha }) => {
        const cosAlpha = Number(utils_1.Utils.math.cos((alpha / 180) * Number(utils_1.Utils.math.PI)));
        return [
            [a / 2, b / 2, 0],
            [-a / 2, b / 2, 0],
            [0, c * cosAlpha, c * Number(utils_1.Utils.math.sqrt(1 - cosAlpha * cosAlpha))],
        ];
    },
    // Algorithm from http://pymatgen.org/_modules/pymatgen/core/lattice.html (from_params)
    TRI: ({ a, b, c, alpha, beta, gamma }) => {
        // convert angles to Radians
        // eslint-disable-next-line no-param-reassign
        [alpha, beta, gamma] = [alpha, beta, gamma].map((x) => Number(utils_1.Utils.math.unit(x, "degree").to("rad").value));
        const [cosAlpha, cosBeta, cosGamma] = [alpha, beta, gamma].map((x) => Number(utils_1.Utils.math.cos(x)));
        const [sinAlpha, sinBeta] = [alpha, beta].map((x) => Number(utils_1.Utils.math.sin(x)));
        let acosArg = (cosAlpha * cosBeta - cosGamma) / (sinAlpha * sinBeta);
        if (acosArg < -1) {
            acosArg = -1;
        }
        else if (acosArg > 1) {
            acosArg = 1;
        }
        const gammaStar = Number(utils_1.Utils.math.acos(acosArg));
        const cosGammaStar = Number(utils_1.Utils.math.cos(gammaStar));
        const sinGammaStar = Number(utils_1.Utils.math.sin(gammaStar));
        return [
            [a * sinBeta, 0.0, a * cosBeta],
            [-b * sinAlpha * cosGammaStar, b * sinAlpha * sinGammaStar, b * cosAlpha],
            [0.0, 0.0, c],
        ];
    },
};
/**
 * Returns lattice vectors for a primitive cell for a lattice.
 * @param latticeConfig - Lattice config.
 * @return Cell.vectorsAsArray
 */
function getPrimitiveLatticeVectorsFromConfig(latticeConfig) {
    const primitiveCellGenerator = PRIMITIVE_CELLS[latticeConfig.type || "TRI"];
    const [vectorA, vectorB, vectorC] = primitiveCellGenerator(latticeConfig);
    return [vectorA, vectorB, vectorC];
}
