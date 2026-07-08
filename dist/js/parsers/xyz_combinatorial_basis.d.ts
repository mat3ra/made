import { BasisSchema } from "@mat3ra/esse/dist/js/types";
import { ElementsAndCoordinatesConfig } from "../basis/basis";
import { AtomicCoordinateValue } from "../basis/coordinates";
import { AtomicElementValue } from "../basis/elements";
import { Cell } from "../cell/cell";
export type ElementWithCoordinate = {
    element: AtomicElementValue;
    coordinate: AtomicCoordinateValue;
};
export declare class WrongBasisFormat extends Error {
    xyz: string;
    constructor(xyz: string, message: string, code: number);
}
export declare class CombinatorialBasis {
    _xyz: string;
    _lines: any[];
    _hasPermutationLine: boolean;
    _hasCombinationLine: boolean;
    constructor(eXYZ: string);
    /**
     * Parses combinatorial basis line and returns result as Object. Throws exception if line is not valid:
     * - does not meet RegExp
     * - mixes permutation and combination
     * @param str {String} Combinatorial basis' line
     * @param index {Number} order of the
     * @return {{displayName: string, isCombination: boolean, isPermutation: boolean, elements: Array, coordinates: *[]}}
     * @private
     */
    _parseBasisLine(str: string, index: number): {
        displayName: string;
        isCombination: boolean;
        isPermutation: boolean;
        elements: string[];
        coordinate: number[];
    };
    /**
     * Returns array of ALL unique elements used in basis.
     * @return {String[]}
     */
    get uniqueElements(): any[];
    static toBasisConfigForElementsAndCoordinates(array: ElementWithCoordinate[], units?: BasisSchema["units"], cell?: Cell): ElementsAndCoordinatesConfig;
    /**
     * Returns array of regular bases extracted from current combinatorial basis.
     * @return {Basis[]|Object[]}
     */
    get allBasisConfigs(): ElementsAndCoordinatesConfig[];
    /**
     * Returns array of regular bases extracted from current combinatorial basis with combinations.
     * @private
     */
    _combination(): ElementWithCoordinate[][];
    /**
     * Returns array of regular bases extracted from current combinatorial basis with permutations.
     * @return {Basis[]}
     * @private
     */
    _permutation(): ElementWithCoordinate[][];
    /**
     * Returns true if current combinatorial basis contains more than one regular basis.
     * @return {Boolean}
     */
    isCombinatorial(): boolean;
}
