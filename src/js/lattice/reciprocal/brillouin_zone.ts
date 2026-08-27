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
 * Shells of reciprocal lattice points considered when bounding the cell. Only the nearest
 * points can contribute a face, so the search is truncated well before the triple loop below
 * becomes expensive.
 */
const MAX_SHELL_INDEX = 2;
const MAX_CANDIDATE_PLANES = 40;

const SINGULAR_MATRIX_TOLERANCE = 1e-9;
const HALF_SPACE_TOLERANCE = 1e-7;
const COINCIDENT_POINT_TOLERANCE = 1e-6;
const ON_PLANE_TOLERANCE = 1e-6;

function crossProduct(first: Vector3DSchema, second: Vector3DSchema): Vector3DSchema {
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ];
}

function dotProduct(first: Vector3DSchema, second: Vector3DSchema): number {
    return first[0] * second[0] + first[1] * second[1] + first[2] * second[2];
}

function subtract(first: Vector3DSchema, second: Vector3DSchema): Vector3DSchema {
    return [first[0] - second[0], first[1] - second[1], first[2] - second[2]];
}

function scale(vector: Vector3DSchema, factor: number): Vector3DSchema {
    return [vector[0] * factor, vector[1] * factor, vector[2] * factor];
}

function vectorLength(vector: Vector3DSchema): number {
    return Math.sqrt(dotProduct(vector, vector));
}

function normalize(vector: Vector3DSchema): Vector3DSchema {
    const magnitude = vectorLength(vector);
    return magnitude === 0 ? [0, 0, 0] : scale(vector, 1 / magnitude);
}

/** Solves `matrix * x = rightHandSide` by Cramer's rule; null when the matrix is singular. */
function solveLinearSystem(
    matrix: [Vector3DSchema, Vector3DSchema, Vector3DSchema],
    rightHandSide: Vector3DSchema,
): Vector3DSchema | null {
    const determinant = dotProduct(matrix[0], crossProduct(matrix[1], matrix[2]));
    if (Math.abs(determinant) < SINGULAR_MATRIX_TOLERANCE) {
        return null;
    }
    const determinantWithColumnReplaced = (columnIndex: 0 | 1 | 2): number => {
        const replaced = matrix.map((row, rowIndex) => {
            const nextRow: Vector3DSchema = [...row];
            nextRow[columnIndex] = rightHandSide[rowIndex];
            return nextRow;
        }) as [Vector3DSchema, Vector3DSchema, Vector3DSchema];
        return dotProduct(replaced[0], crossProduct(replaced[1], replaced[2]));
    };
    return [
        determinantWithColumnReplaced(0) / determinant,
        determinantWithColumnReplaced(1) / determinant,
        determinantWithColumnReplaced(2) / determinant,
    ];
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
export function computeBrillouinZone(
    reciprocalVectors: Vector3DSchema[],
): BrillouinZoneFace[] | null {
    if (reciprocalVectors.length !== 3) {
        return null;
    }
    const [firstVector, secondVector, thirdVector] = reciprocalVectors;
    const isDegenerate = reciprocalVectors.some(
        (vector) => vector.length !== 3 || vector.some((component) => !Number.isFinite(component)),
    );
    if (isDegenerate) {
        return null;
    }

    const latticePoints: Vector3DSchema[] = [];
    for (let first = -MAX_SHELL_INDEX; first <= MAX_SHELL_INDEX; first += 1) {
        for (let second = -MAX_SHELL_INDEX; second <= MAX_SHELL_INDEX; second += 1) {
            for (let third = -MAX_SHELL_INDEX; third <= MAX_SHELL_INDEX; third += 1) {
                if (first !== 0 || second !== 0 || third !== 0) {
                    latticePoints.push([
                        first * firstVector[0] + second * secondVector[0] + third * thirdVector[0],
                        first * firstVector[1] + second * secondVector[1] + third * thirdVector[1],
                        first * firstVector[2] + second * secondVector[2] + third * thirdVector[2],
                    ]);
                }
            }
        }
    }

    const planes = latticePoints
        .sort((left, right) => vectorLength(left) - vectorLength(right))
        .slice(0, MAX_CANDIDATE_PLANES)
        .map((latticePoint) => ({
            normal: latticePoint,
            offset: dotProduct(latticePoint, latticePoint) / 2,
        }));

    const isInsideZone = (point: Vector3DSchema) =>
        planes.every(
            (plane) => dotProduct(point, plane.normal) <= plane.offset + HALF_SPACE_TOLERANCE,
        );

    const vertices: Vector3DSchema[] = [];
    for (let first = 0; first < planes.length; first += 1) {
        for (let second = first + 1; second < planes.length; second += 1) {
            for (let third = second + 1; third < planes.length; third += 1) {
                const point = solveLinearSystem(
                    [planes[first].normal, planes[second].normal, planes[third].normal],
                    [planes[first].offset, planes[second].offset, planes[third].offset],
                );
                const isZoneVertex = point !== null && isInsideZone(point);
                const isDuplicate =
                    isZoneVertex &&
                    vertices.some(
                        (existing) =>
                            vectorLength(subtract(existing, point as Vector3DSchema)) <
                            COINCIDENT_POINT_TOLERANCE,
                    );
                if (isZoneVertex && !isDuplicate) {
                    vertices.push(point as Vector3DSchema);
                }
            }
        }
    }
    if (vertices.length < 4) {
        return null;
    }

    const faces: BrillouinZoneFace[] = [];
    planes.forEach((plane) => {
        const verticesOnPlane = vertices.filter(
            (vertex) =>
                Math.abs(dotProduct(vertex, plane.normal) - plane.offset) < ON_PLANE_TOLERANCE,
        );
        if (verticesOnPlane.length < 3) {
            return;
        }

        // Order the polygon by angle about the face normal, in a basis lying in the face.
        const normal = normalize(plane.normal);
        const centroid = scale(
            verticesOnPlane.reduce<Vector3DSchema>(
                (sum, vertex) => [sum[0] + vertex[0], sum[1] + vertex[1], sum[2] + vertex[2]],
                [0, 0, 0],
            ),
            1 / verticesOnPlane.length,
        );
        const inPlaneAxis = normalize(subtract(verticesOnPlane[0], centroid));
        const inPlaneBitangent = crossProduct(normal, inPlaneAxis);
        const angleAboutNormal = (vertex: Vector3DSchema) => {
            const offsetFromCentroid = subtract(vertex, centroid);
            return Math.atan2(
                dotProduct(offsetFromCentroid, inPlaneBitangent),
                dotProduct(offsetFromCentroid, inPlaneAxis),
            );
        };
        const ordered = [...verticesOnPlane].sort(
            (left, right) => angleAboutNormal(left) - angleAboutNormal(right),
        );
        faces.push({ vertices: ordered, normal });
    });

    return faces.length >= 4 ? faces : null;
}
