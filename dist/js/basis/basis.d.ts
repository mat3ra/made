import { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import { BasisSchema, Coordinate3DSchema, Vector3DSchema, BaseInMemoryEntitySchema } from "@mat3ra/esse/dist/js/types";
import { Cell } from "../cell/cell";
import { AtomicCoordinateValue, Coordinates } from "./coordinates";
import { AtomicElementValue, Elements } from "./elements";
import { AtomicLabelValue, Labels } from "./labels";
export interface ElementWithCoordinate {
    id?: number;
    element: AtomicElementValue;
    coordinate: AtomicCoordinateValue;
}
export interface ElementCount {
    count: number;
    value: AtomicElementValue;
}
interface Overlap {
    id1: number;
    id2: number;
    element1: AtomicElementValue;
    element2: AtomicElementValue;
}
export interface BasisConfig extends BasisSchema {
    cell?: Cell;
    isEmpty?: boolean;
}
export interface ElementsAndCoordinatesConfig {
    elements: AtomicElementValue[];
    coordinates: AtomicCoordinateValue[];
    labels?: AtomicLabelValue[];
    units?: BasisSchema["units"];
    cell?: Cell;
}
type BasisEntitySchema = BasisConfig & BaseInMemoryEntitySchema;
export declare class Basis extends InMemoryEntity<BasisEntitySchema> implements BasisSchema {
    static defaultConfig: BasisSchema;
    units: BasisSchema["units"];
    cell: Cell;
    _elements: Elements;
    _coordinates: Coordinates;
    _labels: Labels;
    static _convertValuesToConfig({ elements, coordinates, units, cell, labels, }: ElementsAndCoordinatesConfig): BasisConfig;
    static fromElementsAndCoordinates({ elements, coordinates, units, cell, labels, }: ElementsAndCoordinatesConfig): Basis;
    constructor(config?: BasisConfig);
    get elements(): BasisSchema["elements"];
    set elements(elements: BasisSchema["elements"]);
    get coordinates(): BasisSchema["coordinates"];
    set coordinates(coordinates: BasisSchema["coordinates"]);
    get labels(): BasisSchema["labels"];
    set labels(labels: BasisSchema["labels"]);
    toJSON(exclude?: (keyof BasisConfig)[]): BasisSchema;
    clone(): this;
    removeAllAtoms(): void;
    get cellRounded(): import("@mat3ra/esse/dist/js/types").Matrix3X3Schema;
    get elementsArray(): object[];
    getElementsAsObject(): BasisSchema["elements"];
    get coordinatesAsArray(): Coordinate3DSchema[];
    get isInCartesianUnits(): boolean;
    get isInCrystalUnits(): boolean;
    toCartesian(): this;
    toCrystal(): this;
    getElementByIndex(idx: number): AtomicElementValue;
    getElementById(id: number): AtomicElementValue;
    getCoordinateValueByIndex(idx: number): AtomicCoordinateValue;
    getCoordinateValueById(id: number): AtomicCoordinateValue;
    toStandardRepresentation(): void;
    /** A representation where all coordinates are within 0 and 1 in crystal units */
    get standardRepresentation(): BasisSchema;
    /**
     * Add atom with a chemical element at coordinate.
     */
    addAtom({ element, coordinate }: ElementWithCoordinate): void;
    /**
     * Remove atom with a chemical element at coordinate either by passing the (element AND coordinate) OR id.
     */
    removeAtom({ element, coordinate, id }: ElementWithCoordinate): void;
    /**
     * Unique names (symbols) of the chemical elements basis. E.g. `['Si', 'Li']`
     */
    get uniqueElements(): AtomicElementValue[];
    /**
     * Returns unique chemical elements with their count sorted by electronegativity.
     * `{ "Fe": 4.0, "O": 8.0, "Li": 2.0}`.
     */
    get uniqueElementCountsSortedByElectronegativity(): import("lodash").Dictionary<number>;
    /**
     * Returns chemical elements with their count wrt their original order in the basis.
     * Note: entries for the same element separated by another element are considered separately.
     * [{"count":1, "value":"Zr"}, {"count":23, "value":"H"}, {"count":11, "value":"Zr"}, {"count":1, "value":"H"}]
     */
    get elementCounts(): ElementCount[];
    /**
     * Reduced formula in IUPAC format. E.g., Na2SO4
     */
    get formula(): string;
    /**
     * Returns the unit cell formula as object `{ "Fe": 4.0, "O": 8.0, "Li": 2.0}`
     */
    get unitCellFormula(): string;
    /**
     * Returns a nested array with elements and their corresponding coordinates
     * @example Output: [ ["Si", [0,0,0]], ["Si", [0.5,0.5,0.5]] ]
     */
    get elementsAndCoordinatesArray(): [AtomicElementValue, AtomicCoordinateValue][];
    /**
     * Returns a nested array with elements and their corresponding coordinates with labels
     * @example Output: [ ["Si", [0,0,0], ['1']], ["Si", [0.5,0.5,0.5]] , ['2']]
     */
    get elementsAndCoordinatesAndLabelsArray(): [
        AtomicElementValue,
        AtomicCoordinateValue,
        AtomicLabelValue
    ][];
    /**
     * @summary Concatenates elements and sorts them in alphanumeric order.
     * E.g.,
     * ```
     *     elements: [{id: 0, value: 'Si'}, {id: 1, value: 'Si'}]
     *     coordinates: [{id: 0, value: [1,0,0]}, {id: 1, value: [0, 1, 0]}]
     *
     *     result: "Si 0,1,0;Si 1,0,0"
     * ```
     * This guarantees the independence from the order in the elements array.
     */
    getAsSortedString(): string;
    /**
     * Returns a string for hash calculation (in crystal units)
     */
    get hashString(): string;
    get atomicLabelsArray(): string[];
    get elementsWithLabelsArray(): string[];
    /**
     * Returns an array of strings with chemical elements and their atomic positions.
     * E.g., ``` ['Si 0 0 0', 'Li 0.5 0.5 0.5']```
     */
    get atomicPositions(): string[];
    /**
     * @summary Returns number of atoms in material
     */
    get nAtoms(): number;
    /**
     * @summary Returns true if bases are equal, otherwise - false.
     * @param anotherBasisClsInstance {Basis} Another Basis.
     */
    isEqualTo(anotherBasisClsInstance: Basis): boolean;
    /**
     * @summary Returns true if basis cells are equal, otherwise - false.
     * @param anotherBasisClsInstance {Basis} Another Basis.
     */
    hasEquivalentCellTo(anotherBasisClsInstance: Basis): boolean;
    /**
     * @summary Returns the minimum cubic lattice size for a non-periodic structure.
     * Single-atom structures use the element atomic radius floored at defaultMinimumLatticeSize.
     * Multi-atom structures scale the maximum pairwise distance by 3 when W=min/max pairwise distance
     * is ~1 (diatomic), otherwise by 2.
     */
    getMinimumLatticeSize(defaultMinimumLatticeSize?: number): number;
    /**
     * @summary function returns an array of overlapping atoms within specified tolerance.
     */
    getOverlappingAtoms(): Overlap[];
    /**
     * @summary function returns the max distance between pairs of basis coordinates by
     * calculating the distance between pairs of basis coordinates.
     * basis coordinates = [[x1, y1, z1], [x2, y2, z2], ... [xn, yn, zn]]
     * n = last set of coordinates
     * n-1 = second to last set of coordinates
     *
     * Iterate through pairs without redundancy.
     *      pair 0,1   pair 0,2  pair 0,3 ... pair 0,n
     *      -          pair 1,2  pair 1,3 ... pair 1,n
     *      -     -    -         pair 2,3 ... pair 2,n
     *      -     -    -         ...      ...
     *      -     -    -         ...      ... pair n-1, n
     *
     */
    get maxPairwiseDistance(): number;
    get minPairwiseDistance(): number;
    getPairwiseDistanceExtremum(extremum: "max" | "min"): number;
    /**
     * @summary Function takes basis coordinates and transposes them so that the values for each dimension of the
     *  the basis are in their own nested array.
     *  Then the center point for each dimension of the coordinates is calculated.
     *
     * initial basisCoordinates
     * [[x1, y1, z1],
     *  [x2, y2, z2],
     *  [.., .., ..],
     *  [xn, yn, zn]]
     *
     * transposed basisCoordinates
     * [[x1, x2, ...xn],
     *  [y1, y2, ...yn],
     *  [z1, z2, ...zn]]
     *
     * Returns an array = [xCenter, yCenter, zCenter]
     */
    get centerOfCoordinatesPoint(): AtomicCoordinateValue;
    /**
     * @summary Function translates coordinates by the vector passed as an argument.
     */
    translateByVector(translationVector: Vector3DSchema): void;
}
export {};
