import { Vector3DSchema } from "@mat3ra/esse/dist/js/types";
import { Lattice } from "../lattice";
import { BrillouinZoneFace } from "./brillouin_zone";
export type KPointCoordinates = number[];
export type KPointPath = Array<{
    point: string;
    steps: number;
    coordinates: KPointCoordinates;
}>;
interface SymmetryPoint {
    point: string;
    coordinates: KPointCoordinates;
}
interface ConversionTable {
    [key: string]: {
        [key: string]: number;
    };
}
export declare class ReciprocalLattice extends Lattice {
    /**
     * Get reciprocal vectors for the current Lattice in cartesian (2pi / a) units
     * @return {Vector3DSchema[]}
     */
    get reciprocalVectors(): Vector3DSchema[];
    /**
     * Norms of reciprocal vectors.
     */
    get reciprocalVectorNorms(): Vector3DSchema;
    /**
     * Ratio of reciprocal vector norms scaled by the inverse of the largest component.
     */
    get reciprocalVectorRatios(): Vector3DSchema;
    /**
     * Get point (in crystal coordinates) in cartesian coordinates.
     * @param {KPointCoordinates} point - point in 3D space
     * @return {KPointCoordinates}
     */
    getCartesianCoordinates(point: KPointCoordinates): KPointCoordinates;
    /**
     * Get the list of high-symmetry points for the current lattice.
     * @return {SymmetryPoint[]}
     */
    get symmetryPoints(): SymmetryPoint[];
    /**
     * Get the first Brillouin zone — the Wigner-Seitz cell of the reciprocal lattice — as a
     * list of polygonal faces, ready to be projected and drawn.
     *
     * The zone follows from this lattice's own vectors rather than from its Bravais type, so
     * materials sharing a type but differing in axial ratios (a bulk crystal and a slab with
     * vacuum padding, say) yield correctly differing zones.
     *
     * @return {BrillouinZoneFace[] | null} null for a degenerate lattice.
     */
    get brillouinZone(): BrillouinZoneFace[] | null;
    /**
     * Get the default path in reciprocal space for the current lattice.
     * @return {Array<{point: string; steps: number}>}
     */
    get defaultKpointPath(): Array<{
        point: string;
        steps: number;
    }>;
    /**
     * Find/mark the high symmetry points on a list with raw data and return the edited list.
     * @param {KPointCoordinates[]} dataPoints - list of point coordinates
     * @return {KPointPath}
     */
    extractKpointPath(dataPoints?: KPointCoordinates[]): KPointPath;
    /**
     * Calculate grid dimension based on reciprocal lattice vectors.
     * @param {number} nPoints - Total number of points
     * @param {number} index - Index of reciprocal vector
     * @return {number} - Grid dimension in direction of reciprocal vector
     * @todo This could be moved to a separate KGrid class.
     */
    calculateDimension(nPoints: number, index: number): number;
    /**
     * Calculate grid dimensions from total number of k-points.
     * @param {number} nKpoints - Total number of k-points.
     * @return Grid dimensions
     */
    getDimensionsFromPointsCount(nKpoints: number): Vector3DSchema;
    get conversionTable(): ConversionTable;
    /**
     * Calculate grid dimensions from k-point spacing, i.e.
     * the maximum distance between adjacent points along a reciprocal axis.
     * Note: just as the lattice vectors spacing is in cartesian (2pi / a) units by default
     * @param {number} spacing - maximum Spacing between k-points
     * @param {string} units - units of spacing parameter (default: 2pi / a)
     */
    getDimensionsFromSpacing(spacing: number, units?: string): Vector3DSchema;
    /**
     * Calculate grid spacing as average of spacing along individual reciprocal axes.
     * @param {number[]} dimensions - Array of dimensions
     * @param {string} units - units of spacing parameter (default: 2pi / a)
     * @return {number} - average grid spacing
     */
    getSpacingFromDimensions(dimensions: number[], units?: string): number;
}
export {};
