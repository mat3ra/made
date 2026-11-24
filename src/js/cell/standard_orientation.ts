import { LatticeSchema, LatticeTypeEnum, Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";

import { PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS } from "./conventional_cell";
import { getPrimitiveLatticeVectorsFromConfig } from "./primitive_cell";

/**
 * Primitive lattice vectors in the standard orientation of their lattice type.
 * Python equivalent: src/py/mat3ra/made/cell/standard_orientation.py.
 *
 * Lattice parameters (a, b, c, alpha, beta, gamma) fix the shape of a cell but not its
 * orientation. The generic construction places the third vector along z and the first in
 * the xz plane for every type, which leaves the symmetry axes of most centred lattices
 * tilted away from x, y and z. The standard primitive cells of Setyawan and Curtarolo
 * (doi:10.1016/j.commatsci.2010.05.010) have the conventional axes along x, y and z.
 * Programs that look for symmetry only about the Cartesian axes, such as Quantum
 * ESPRESSO's pw.x with explicit cell vectors, find the full point group only there.
 *
 * A rigid rotation changes no lengths or angles, so fractional coordinates stay valid.
 */

const TOLERANCE = 1e-6;

function angleInDegrees(first: number[], second: number[]): number {
    const cosine =
        Utils.math.dot(first, second) / (Utils.math.vlen(first) * Utils.math.vlen(second));
    return (Math.acos(Math.max(-1, Math.min(1, cosine))) * 180) / Math.PI;
}

/**
 * The conventional cell parameters of primitive `vectors` of `latticeType`.
 *
 * The conventional vectors are the type's multiplier times the primitive ones; alpha is
 * the angle between the second and third, as the monoclinic standard cells use it.
 */
export function getConventionalParameters(
    vectors: Matrix3X3Schema,
    latticeType: LatticeTypeEnum,
): LatticeSchema {
    const multiplier = PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS[latticeType];
    const conventional = Utils.math.multiply(multiplier, vectors) as unknown as number[][];
    return {
        a: Utils.math.vlen(conventional[0]),
        b: Utils.math.vlen(conventional[1]),
        c: Utils.math.vlen(conventional[2]),
        alpha: angleInDegrees(conventional[1], conventional[2]),
        beta: angleInDegrees(conventional[0], conventional[2]),
        gamma: angleInDegrees(conventional[0], conventional[1]),
        type: latticeType,
    } as LatticeSchema;
}

function isProperRotation(rotation: number[][]): boolean {
    const product = Utils.math.multiply(Utils.math.transpose(rotation), rotation) as number[][];
    const isOrthogonal = product.every((row, i) =>
        row.every((value, j) => Math.abs(value - (i === j ? 1 : 0)) <= TOLERANCE),
    );
    return isOrthogonal && (Utils.math.det(rotation) as number) > 0;
}

/**
 * `vectors` rotated rigidly onto the standard primitive cell of `latticeType`.
 *
 * The rotation R solves vectors · R = standard. The standard cell is used only when R is
 * a proper rotation, which holds when `vectors` are the type's primitive vectors in the
 * standard choice and order; otherwise, for a lattice whose shape does not match its
 * type, or that matches only by a reflection, `vectors` are returned unchanged.
 */
export function getVectorsInStandardOrientation(
    vectors: Matrix3X3Schema,
    latticeType?: LatticeTypeEnum,
): Matrix3X3Schema {
    if (!latticeType || !(latticeType in PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS))
        return vectors;
    const parameters = getConventionalParameters(vectors, latticeType);
    const standard = getPrimitiveLatticeVectorsFromConfig(parameters);
    const rotation = Utils.math.multiply(
        Utils.math.inv(vectors),
        standard,
    ) as unknown as number[][];
    return isProperRotation(rotation) ? standard : vectors;
}
