import { Coordinate3DSchema, Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";

import { Basis, BasisConfig } from "../basis/basis";
import { Cell } from "../cell/cell";
import { Lattice } from "../lattice/lattice";
import type { MaterialSchemaMap } from "../Material";
import type Material from "../Material";
import cellTools from "./cell";

const ADD = Utils.math.add;

/**
 * @summary Generates new basis for a supercell. For each site from basis generates shifts that are within supercell.
 */
function generateNewBasisWithinSupercell<S extends BasisConfig>(
    basis: Basis<S>,
    cell: Cell,
    supercell: Cell,
    supercellMatrix: Matrix3X3Schema,
): Basis<S> {
    const newBasis = basis.clone();
    newBasis.toCrystal();
    const originalAtomIds = newBasis.elements.map(({ id }) => id);

    originalAtomIds.forEach((id) => {
        const coordinate = newBasis.getCoordinateValueById(id);
        const cartesianCoordinate = cell.convertPointToCartesian(coordinate);
        const shifts = cellTools.latticePointsInSupercell(supercellMatrix);
        shifts.forEach((combination) => {
            // "combination" is effectively a point in fractional coordinates here, hence the below
            const newPoint = ADD(
                cartesianCoordinate,
                supercell.convertPointToCartesian(combination),
            );
            if (supercell.isPointInsideCell(newPoint as Coordinate3DSchema)) {
                newBasis.addCopyOfAtom(
                    id,
                    supercell.convertPointToCrystal(
                        newPoint as Coordinate3DSchema,
                    ) as Coordinate3DSchema,
                );
            }
        });
    });

    // keep only the copies, numbered from 0
    return newBasis.filterAtomsByIds(originalAtomIds, true, true);
}

/**
 * @summary Generates supercell config for the specified material.
 */
function generateConfig<Schemas extends MaterialSchemaMap = MaterialSchemaMap>(
    material: Material<Schemas>,
    supercellMatrix: Matrix3X3Schema,
) {
    const det = Utils.math.det(supercellMatrix);
    if (det === 0) {
        throw new Error("Scaling matrix is degenerate.");
    }
    const cell = material.getLattice().vectors;
    const supercell = cell.cloneAndScaleByMatrix(supercellMatrix);
    const newBasis = generateNewBasisWithinSupercell(
        material.getBasis(),
        cell,
        supercell,
        supercellMatrix,
    );
    const newLattice = Lattice.fromVectors({
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

export default {
    generateConfig,
    generateNewBasisWithinSupercell,
};
