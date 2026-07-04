import { LatticeSchema, Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const math: any = Utils.math;


/**
 * Routines for calculating primitive cell vectors from conventional cell Bravais parameters.
 * Following Setyawan, W., & Curtarolo, S. (2010). doi:10.1016/j.commatsci.2010.05.010
 */
const PRIMITIVE_CELLS = {
    CUB: ({ a }: LatticeSchema): Matrix3X3Schema => {
        return [
            [a, 0, 0],
            [0, a, 0],
            [0, 0, a],
        ];
    },

    FCC: ({ a }: LatticeSchema): Matrix3X3Schema => {
        return [
            [0.0, a / 2, a / 2],
            [a / 2, 0.0, a / 2],
            [a / 2, a / 2, 0.0],
        ];
    },

    BCC: ({ a }: LatticeSchema): Matrix3X3Schema => {
        return [
            [-a / 2, a / 2, a / 2],
            [a / 2, -a / 2, a / 2],
            [a / 2, a / 2, -a / 2],
        ];
    },

    TET: ({ a, c }: LatticeSchema): Matrix3X3Schema => {
        return [
            [a, 0, 0],
            [0, a, 0],
            [0, 0, c],
        ];
    },

    BCT: ({ a, c }: LatticeSchema): Matrix3X3Schema => {
        return [
            [-a / 2, a / 2, c / 2],
            [a / 2, -a / 2, c / 2],
            [a / 2, a / 2, -c / 2],
        ];
    },

    ORC: ({ a, b, c }: LatticeSchema): Matrix3X3Schema => {
        return [
            [a, 0, 0],
            [0, b, 0],
            [0, 0, c],
        ];
    },

    ORCF: ({ a, b, c }: LatticeSchema): Matrix3X3Schema => {
        return [
            [0, b / 2, c / 2],
            [a / 2, 0, c / 2],
            [a / 2, b / 2, 0],
        ];
    },

    ORCI: ({ a, b, c }: LatticeSchema): Matrix3X3Schema => {
        return [
            [-a / 2, b / 2, c / 2],
            [a / 2, -b / 2, c / 2],
            [a / 2, b / 2, -c / 2],
        ];
    },

    ORCC: ({ a, b, c }: LatticeSchema): Matrix3X3Schema => {
        return [
            [a / 2, b / 2, 0],
            [-a / 2, b / 2, 0],
            [0, 0, c],
        ];
    },

    HEX: ({ a, c }: LatticeSchema): Matrix3X3Schema => {
        return [
            [a / 2, (-a * math.sqrt(3)) / 2, 0],
            [a / 2, (a * math.sqrt(3)) / 2, 0],
            [0, 0, c],
        ];
    },

    RHL: ({ a, alpha }: LatticeSchema): Matrix3X3Schema => {
        const cosAlpha = math.cos((alpha / 180) * math.PI);
        const cosHalfAlpha = math.sqrt((1 / 2) * (1 + cosAlpha));
        const sinHalfAlpha = math.sqrt((1 / 2) * (1 - cosAlpha));
        return [
            [a * cosHalfAlpha, -a * sinHalfAlpha, 0.0],
            [a * cosHalfAlpha, a * sinHalfAlpha, 0.0],
            [
                (a * cosAlpha) / cosHalfAlpha,
                0.0,
                a * math.sqrt(1 - (cosAlpha * cosAlpha) / (cosHalfAlpha * cosHalfAlpha)),
            ],
        ];
    },

    MCL: ({ a, b, c, alpha }: LatticeSchema): Matrix3X3Schema => {
        const cosAlpha = math.cos((alpha / 180) * math.PI);
        return [
            [a, 0, 0],
            [0, b, 0],
            [0, c * cosAlpha, c * math.sqrt(1 - cosAlpha * cosAlpha)],
        ];
    },

    MCLC: ({ a, b, c, alpha }: LatticeSchema): Matrix3X3Schema => {
        const cosAlpha = math.cos((alpha / 180) * math.PI);
        return [
            [a / 2, b / 2, 0],
            [-a / 2, b / 2, 0],
            [0, c * cosAlpha, c * math.sqrt(1 - cosAlpha * cosAlpha)],
        ];
    },

    // Algorithm from http://pymatgen.org/_modules/pymatgen/core/lattice.html (from_params)
    TRI: ({ a, b, c, alpha, beta, gamma }: LatticeSchema): Matrix3X3Schema => {
        // convert angles to Radians
        // eslint-disable-next-line no-param-reassign
        [alpha, beta, gamma] = [alpha, beta, gamma].map(
            // @ts-ignore
            (x) => math.unit(x, "degree").to("rad").value,
        );

        const [cosAlpha, cosBeta, cosGamma] = [alpha, beta, gamma].map((x) => math.cos(x));
        const [sinAlpha, sinBeta] = [alpha, beta].map((x) => math.sin(x));
        let acosArg = (cosAlpha * cosBeta - cosGamma) / (sinAlpha * sinBeta);
        if (acosArg < -1) {
            acosArg = -1;
        } else if (acosArg > 1) {
            acosArg = 1;
        }
        const gammaStar = math.acos(acosArg);
        const cosGammaStar = math.cos(gammaStar);
        const sinGammaStar = math.sin(gammaStar);

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
export function getPrimitiveLatticeVectorsFromConfig(
    latticeConfig: LatticeSchema,
): Matrix3X3Schema {
    const primitiveCellGenerator = PRIMITIVE_CELLS[latticeConfig.type || "TRI"];
    const [vectorA, vectorB, vectorC] = primitiveCellGenerator(latticeConfig);
    return [vectorA, vectorB, vectorC];
}
