import { Coordinate3DSchema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { chunk, flatten } from "lodash";

import { Basis, BasisConfig } from "../basis/basis";
import { AtomicCoordinateValue } from "../basis/coordinates";

const ADD = Utils.math.add;
const MULT = Utils.math.multiply;

/**
 * Returns a repeated basis of a crystal.
 * @param basis {Basis} Original basis.
 * @param repetitions{Number[]} Repetition vector `[x, y, z]`, in each spatial dimension.
 * @return {Basis} New Basis.
 */
function repeat<S extends BasisConfig>(basis: Basis<S>, repetitions: number[]): Basis<S> {
    let i, j, k;
    let shiftI = 0;
    let shiftJ = 0;
    let shiftK = 0;

    // clone original basis and convert it to crystal coordinates
    const newBasis = basis.clone();
    const basisCloneInCrystalCoordinates = basis.clone();

    newBasis.toCrystal();
    basisCloneInCrystalCoordinates.toCrystal();

    for (i = 1; i <= repetitions[0]; i += 1) {
        for (j = 1; j <= repetitions[1]; j += 1) {
            for (k = 1; k <= repetitions[2]; k += 1) {
                // only add atoms if shifts are non-zero
                if (shiftI || shiftJ || shiftK) {
                    const repetition = basisCloneInCrystalCoordinates.clone();
                    repetition.translateByVector([shiftI, shiftJ, shiftK]);
                    newBasis.addAtomsFromAnotherBasis(repetition);
                }
                shiftK += 1;
            }
            shiftK = 0;
            shiftJ += 1;
        }
        shiftJ = 0;
        shiftI += 1;
    }

    if (basis.isInCartesianUnits) newBasis.toCartesian();

    return newBasis;
}

/**
 * Calculates linear function `y = kx + b` for vectors. Isolated for modularity.
 * @param initialCoordinate {Array} - b.
 * @param delta {Array} - x.
 * @param normalizedStepIndex {Number} - k.
 * @return {Basis[]} List of all bases.
 */
function _linearInterpolation(
    initialCoordinate: AtomicCoordinateValue,
    delta: Coordinate3DSchema,
    normalizedStepIndex: number,
): number[] {
    return ADD(initialCoordinate, MULT(delta, normalizedStepIndex)) as number[];
}

/**
 * Returns a set of Bases for a crystal interpolated from initial to final crystal.
 *          Can be used to generate atomic configurations along a chemical reaction path, for example.
 * @param initialBasis {Basis} Original initialBasis.
 * @param finalBasis {Basis} Final basis.
 * @param numberOfSteps{Number} Number of intermediate steps.
 * @return {Basis[]} List of all bases.
 */
function interpolate<S extends BasisConfig>(
    initialBasis: Basis<S>,
    finalBasis: Basis<S>,
    numberOfSteps = 1,
) {
    // check that initial and final basis have the same cell
    if (!initialBasis.hasEquivalentCellTo(finalBasis))
        throw new Error("basis.interpolate: Basis cells are not equal");

    // clone both bases and convert them to crystal coordinates
    const initialBasisCopy = initialBasis.clone();
    const finalBasisCopy = finalBasis.clone();

    initialBasisCopy.toCrystal();
    finalBasisCopy.toCrystal();

    const initialCoordinates = flatten(initialBasisCopy.coordinatesAsArray);
    const finalCoordinates = flatten(finalBasisCopy.coordinatesAsArray);
    const delta = ADD(finalCoordinates, MULT(initialCoordinates, -1));
    const resultingListOfBases = [];

    for (let i = 1; i <= numberOfSteps; i++) {
        const normalizedStepIndex = i / (numberOfSteps + 1);
        const intermediateCoordinates: number[] = _linearInterpolation(
            initialCoordinates as AtomicCoordinateValue,
            delta as AtomicCoordinateValue,
            normalizedStepIndex,
        );
        const vectorSize = 3;
        const intermediateCoordinatesAsNestedArray = chunk(intermediateCoordinates, vectorSize);
        const intermediateBasis = initialBasisCopy.clone();
        intermediateBasis.coordinates = intermediateCoordinatesAsNestedArray.map(
            (coordinate, index) => ({
                id: initialBasisCopy._coordinates.ids[index],
                value: coordinate as AtomicCoordinateValue,
            }),
        );
        if (initialBasis.isInCartesianUnits) intermediateBasis.toCartesian();

        resultingListOfBases.push(intermediateBasis);
    }

    return resultingListOfBases;
}

export default {
    repeat,
    interpolate,
};
