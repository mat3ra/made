"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PRIMITIVE_TO_CONVENTIONAL_CELL_LATTICE_TYPES = exports.PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS = void 0;
exports.isConventionalCellSameAsPrimitiveForLatticeType = isConventionalCellSameAsPrimitiveForLatticeType;
/**
 * Routines for calculating conventional cell vectors from primitive cell Bravais parameters.
 * Following Setyawan, W., & Curtarolo, S. (2010). doi:10.1016/j.commatsci.2010.05.010
 */
const unitMatrix = [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
];
// (Conventional cellVectors) = (Primitive cellVectors) * (PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIER matrix)
exports.PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS = {
    // PRIMITIVE    =>  CONVENTIONAL
    CUB: unitMatrix,
    FCC: [
        [-1, 1, 1],
        [1, -1, 1],
        [1, 1, -1],
    ],
    BCC: [
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0],
    ],
    TET: unitMatrix,
    BCT: [
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0],
    ],
    ORC: unitMatrix,
    ORCF: [
        [-1, 1, 1],
        [1, -1, 1],
        [1, 1, -1],
    ],
    ORCI: [
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0],
    ],
    ORCC: [
        [1, -1, 0],
        [1, 1, 0],
        [0, 0, 1],
    ],
    HEX: unitMatrix,
    RHL: unitMatrix,
    MCL: unitMatrix,
    MCLC: [
        [1, -1, 0],
        [1, 1, 0],
        [0, 0, 1],
    ],
    TRI: unitMatrix,
};
exports.PRIMITIVE_TO_CONVENTIONAL_CELL_LATTICE_TYPES = {
    // PRIMITIVE    =>  CONVENTIONAL
    CUB: "CUB",
    FCC: "CUB",
    BCC: "CUB",
    TET: "TET",
    BCT: "TET",
    ORC: "ORC",
    ORCF: "ORC",
    ORCI: "ORC",
    ORCC: "ORC",
    HEX: "HEX",
    RHL: "RHL",
    MCL: "MCL",
    MCLC: "MCL",
    TRI: "TRI",
};
function isConventionalCellSameAsPrimitiveForLatticeType(latticeType) {
    const multiplier = exports.PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS[latticeType || "TRI"];
    return multiplier === unitMatrix;
}
