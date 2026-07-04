"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const utils_1 = require("@mat3ra/utils");
const cell_1 = require("../cell/cell");
/**
 * Returns the list of points on the original lattice contained in the supercell in fractional coordinates.
 * Source: https://pymatgen.org/_modules/pymatgen/util/coord.html
 */
function latticePointsInSupercell(supercellMatrix) {
    const supercell = cell_1.Cell.fromVectorsArray(supercellMatrix);
    const diagonals = [
        [0, 0, 0],
        [0, 0, 1],
        [0, 1, 0],
        [0, 1, 1],
        [1, 0, 0],
        [1, 0, 1],
        [1, 1, 0],
        [1, 1, 1],
    ];
    const d_points = diagonals.map((point) => supercell.convertPointToCartesian(point));
    const mins = [0, 1, 2].map((i) => utils_1.Utils.math.min(...d_points.map((p) => p[i])));
    const maxes = [0, 1, 2].map((i) => utils_1.Utils.math.max(...d_points.map((p) => p[i])) + 1);
    const points = [];
    for (let i = mins[0]; i <= maxes[0]; i++) {
        for (let j = mins[1]; j <= maxes[1]; j++) {
            for (let k = mins[2]; k <= maxes[2]; k++) {
                points.push(supercell.convertPointToCrystal([i, j, k]));
            }
        }
    }
    return points;
}
exports.default = {
    latticePointsInSupercell,
};
