import { Coordinate3DSchema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { chunk, flatten } from "lodash";

import { Basis } from "../basis/basis";
import { AtomicCoordinateValue, Coordinate } from "../basis/coordinates";


const ADD = Utils.math.add;
const MULT = Utils.math.multiply;

/**
 * Returns a repeated basis of a crystal.
 * @param basis {Basis} Original basis.
 * @param repetitions{Number[]} Repetition vector `[x, y, z]`, in each spatial dimension.
 * @return {Basis} New Basis.
 */
function repeat(basis: Basis, repetitions: number[]): Basis {
    let i, j, k;
    let shiftI = 0;
    let shiftJ = 0;
    let shiftK = 0;

    // clone original basis and assert it is in cartesian coordinates
    const newBasis = basis.clone();
    const basisCloneInCrystalCoordinates = basis.clone();

    newBasis.toCrystal();
    basisCloneInCrystalCoordinates.toCrystal();

    for (i = 1; i <= repetitions[0]; i += 1) {
        for (j = 1; j <= repetitions[1]; j += 1) {
            for (k = 1; k <= repetitions[2]; k += 1) {
                // for each atom in original basis add one with a repetition
                // eslint-disable-next-line no-loop-func
                basisCloneInCrystalCoordinates.elements.forEach((element, index) => {
                    const coord = basisCloneInCrystalCoordinates.getCoordinateValueByIndex(index);
                    // only add atoms if shifts are non-zero
                    if (shiftI || shiftJ || shiftK) {
                        const coordinateInstance = Coordinate.fromValueAndId(coord);
                        const translatedCoordinateInstance = coordinateInstance.translateByVector([
                            shiftI,
                            shiftJ,
                            shiftK,
                        ]);
                        newBasis.addAtom({
                            element: element.value,
                            coordinate: translatedCoordinateInstance.value,
                        });
                    }
                });
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
 * @param finalBasis {Basis} Final initialBasis.
 * @param numberOfSteps{Number} Number of intermediate steps.
 * @return {Basis[]} List of all bases.
 */
function interpolate(initialBasis: Basis, finalBasis: Basis, numberOfSteps = 1) {
    // check that initial and final basis have the same cell
    if (!initialBasis.hasEquivalentCellTo(finalBasis))
        throw new Error("basis.interpolate: Basis cells are not equal");

    // clone original initialBasis and assert it is in cartesian coordinates
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
        const intermediateBasis = initialBasis.clone();
        intermediateBasis.coordinates = intermediateCoordinatesAsNestedArray.map(
            (coordinate, index) => ({
                id: index,
                value: coordinate as AtomicCoordinateValue,
            }),
        );

        resultingListOfBases.push(intermediateBasis);
    }

    return resultingListOfBases;
}

export default {
    repeat,
    interpolate,
};
