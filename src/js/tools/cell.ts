import { Coordinate3DSchema, Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";

import { Cell } from "../cell/cell";


/**
 * Returns the list of points on the original lattice contained in the supercell in fractional coordinates.
 * Source: https://pymatgen.org/_modules/pymatgen/util/coord.html
 */
function latticePointsInSupercell(supercellMatrix: Matrix3X3Schema) {
    const supercell = Cell.fromVectorsArray(supercellMatrix);
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
    const d_points = diagonals.map((point) =>
        supercell.convertPointToCartesian(point as Coordinate3DSchema),
    );
    const mins = [0, 1, 2].map((i) => Utils.math.min(...d_points.map((p) => p[i])));
    const maxes = [0, 1, 2].map((i) => Utils.math.max(...d_points.map((p) => p[i])) + 1);
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

export default {
    latticePointsInSupercell,
};
