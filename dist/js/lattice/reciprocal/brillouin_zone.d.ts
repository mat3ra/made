import { Vector3DSchema } from "@mat3ra/esse/dist/js/types";
/**
 * A face of the first Brillouin zone: the polygon cut by the perpendicular bisector plane
 * ("Bragg plane") of one reciprocal lattice vector.
 */
export interface BrillouinZoneFace {
    /** Polygon vertices in reciprocal space, ordered counter-clockwise about `normal`. */
    vertices: Vector3DSchema[];
    /** Outward unit normal, along the reciprocal lattice vector bounding this face. */
    normal: Vector3DSchema;
}
/**
 * Computes the first Brillouin zone — the Wigner-Seitz cell of the reciprocal lattice.
 *
 * The zone is the set of points closer to the origin than to any other reciprocal lattice
 * point `G`, i.e. the intersection of the half-spaces `k · G <= |G|^2 / 2`. Its vertices are
 * the points where three bounding planes meet while satisfying every other half-space, and its
 * faces group the vertices lying on each plane.
 *
 * The shape follows from the lattice itself, not from its Bravais type: two materials of the
 * same type but different axial ratios (a bulk crystal and a slab with vacuum padding, say)
 * have differently proportioned zones.
 *
 * @param reciprocalVectors - the three reciprocal lattice vectors, e.g.
 *                            `new ReciprocalLattice(material.lattice).reciprocalVectors`.
 * @returns the zone's faces, or null when the vectors are degenerate (coplanar or zero).
 */
export declare function computeBrillouinZone(reciprocalVectors: Vector3DSchema[]): BrillouinZoneFace[] | null;
