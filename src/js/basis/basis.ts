// @ts-ignore
import { getElectronegativity, getElementAtomicRadius } from "@exabyte-io/periodic-table.js";
import { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import { BasisSchema, Coordinate3DSchema, Vector3DSchema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { chain, toPairs, uniq, values } from "lodash";

import { Cell } from "../cell/cell";
import { ATOMIC_COORD_UNITS, HASH_TOLERANCE } from "../constants";

import {
    defaultNonPeriodicMinimumLatticeSize,
    diatomicLatticePaddingFactor,
    molecularLatticePaddingFactor,
} from "../lattice/lattice";
import { AtomicCoordinateValue, Coordinates } from "./coordinates";
import { AtomicElementValue, Elements } from "./elements";
import { AtomicLabelValue, Labels } from "./labels";

export interface ElementWithCoordinate {
    id?: number; // numeric id of the element (optional).
    element: AtomicElementValue; // Chemical element
    coordinate: AtomicCoordinateValue; // Coordinates of the element
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

const DEFAULT_BASIS_CONFIG = {
    elements: [
        {
            id: 0,
            value: "Si",
        },
        {
            id: 1,
            value: "Si",
        },
    ],
    coordinates: [
        {
            id: 0,
            value: [0, 0, 0],
        },
        {
            id: 1,
            value: [0.25, 0.25, 0.25],
        },
    ],
    units: "crystal",
};

export class Basis extends InMemoryEntity implements BasisSchema {
    static defaultConfig: BasisSchema = DEFAULT_BASIS_CONFIG as BasisSchema;

    units: BasisSchema["units"];

    cell: Cell;

    _elements: Elements;

    _coordinates: Coordinates;

    _labels: Labels;

    static _convertValuesToConfig({
        elements = [],
        coordinates = [],
        units = ATOMIC_COORD_UNITS.crystal as BasisSchema["units"],
        cell = new Cell(),
        labels = [],
    }: ElementsAndCoordinatesConfig): BasisConfig {
        const elementsArrayWithIdsJSON = Elements.fromValues(elements).toJSON();
        const coordinatesArrayWithIdsJSON = Coordinates.fromValues(coordinates).toJSON();
        const labelsArrayWithIdsJSON = Labels.fromValues(labels).toJSON();
        return {
            elements: elementsArrayWithIdsJSON as BasisSchema["elements"],
            coordinates: coordinatesArrayWithIdsJSON as BasisSchema["coordinates"],
            units,
            cell,
            labels: labelsArrayWithIdsJSON as BasisSchema["labels"],
        };
    }

    static fromElementsAndCoordinates({
        elements = [],
        coordinates = [],
        units = ATOMIC_COORD_UNITS.crystal as BasisSchema["units"],
        cell = new Cell(),
        labels = [],
    }: ElementsAndCoordinatesConfig): Basis {
        return new Basis(
            Basis._convertValuesToConfig({
                elements,
                coordinates,
                units,
                cell,
                labels,
            }),
        );
    }

    constructor(config: BasisConfig = Basis.defaultConfig) {
        super(config);
        const { elements, coordinates, units, labels } = config;
        this.cell = new Cell(config.cell);
        this.units = units || (ATOMIC_COORD_UNITS.crystal as BasisSchema["units"]);
        this._elements = Elements.fromObjects(elements);
        this._coordinates = Coordinates.fromObjects(coordinates);
        this._labels = Labels.fromObjects(labels || []);
    }

    get elements(): BasisSchema["elements"] {
        return this._elements.toJSON() as BasisSchema["elements"];
    }

    set elements(elements: BasisSchema["elements"]) {
        this._elements = Elements.fromObjects(elements);
    }

    get coordinates(): BasisSchema["coordinates"] {
        return this._coordinates.toJSON() as BasisSchema["coordinates"];
    }

    set coordinates(coordinates: BasisSchema["coordinates"]) {
        this._coordinates = Coordinates.fromObjects(coordinates);
    }

    get labels(): BasisSchema["labels"] {
        return this._labels.toJSON() as BasisSchema["labels"];
    }

    set labels(labels: BasisSchema["labels"]) {
        this._labels = Labels.fromObjects(labels || []);
    }

    // TODO: figure out how to override toJSON in the parent class with generic classes
    // @ts-ignore
    toJSON(exclude: string[] = ["cell"]): BasisSchema {
        return {
            ...super.toJSON(exclude),
            elements: this.elements,
            coordinates: this.coordinates,
            units: this.units,
            ...(this.labels?.length ? { labels: this.labels } : {}),
        };
    }

    // @ts-ignore
    override clone(): Basis {
        const instance = super.clone();
        instance.cell = this.cell.clone();
        return instance;
    }

    removeAllAtoms() {
        this.elements = [];
        this.coordinates = [];
        this.labels = [];
    }

    get cellRounded() {
        return this.cell.vectorArraysRounded;
    }

    get elementsArray(): object[] {
        return this._elements.toJSON();
    }

    getElementsAsObject(): BasisSchema["elements"] {
        return this.elements;
    }

    get coordinatesAsArray() {
        return this._coordinates.values;
    }

    get isInCartesianUnits(): boolean {
        return this.units === ATOMIC_COORD_UNITS.cartesian;
    }

    get isInCrystalUnits(): boolean {
        return this.units === ATOMIC_COORD_UNITS.crystal;
    }

    toCartesian(): void {
        if (this.isInCartesianUnits) return;
        this._coordinates.mapArrayInPlace((point) => this.cell.convertPointToCartesian(point));
        this.units = ATOMIC_COORD_UNITS.cartesian as BasisSchema["units"];
    }

    toCrystal(): void {
        if (this.isInCrystalUnits) return;
        this._coordinates.mapArrayInPlace((point) => this.cell.convertPointToCrystal(point));
        this.units = ATOMIC_COORD_UNITS.crystal as BasisSchema["units"];
    }

    getElementByIndex(idx: number): AtomicElementValue {
        return this._elements.getElementValueByIndex(idx) as AtomicElementValue;
    }

    getElementById(id: number): AtomicElementValue {
        const result = this._elements.getElementValueById(id) as AtomicElementValue;
        if (result) {
            return result;
        }
        throw new Error(`Element with index ${id} not found`);
    }

    getCoordinateValueByIndex(idx: number): AtomicCoordinateValue {
        const value = this._coordinates.getElementValueByIndex(idx);
        if (value) {
            return value as AtomicCoordinateValue;
        }
        throw new Error(`Coordinate with index ${idx} not found`);
    }

    getCoordinateValueById(id: number): AtomicCoordinateValue {
        const coordinate = this._coordinates.getElementValueById(id);
        if (coordinate) {
            return coordinate as AtomicCoordinateValue;
        }
        throw new Error(`Coordinate with index ${id} not found`);
    }

    toStandardRepresentation() {
        this.toCrystal();
        this._coordinates.mapArrayInPlace(
            (point) => point.map((x) => Utils.math.mod(x)) as Coordinate3DSchema,
        );
    }

    /** A representation where all coordinates are within 0 and 1 in crystal units */
    get standardRepresentation(): BasisSchema {
        const originalIsInCartesianUnits = this.isInCartesianUnits;

        this.toStandardRepresentation();
        const result = this.toJSON();

        if (originalIsInCartesianUnits) this.toCartesian();

        return result as BasisSchema;
    }

    /**
     * Add atom with a chemical element at coordinate.
     */
    addAtom({ element = "Si", coordinate = [0.5, 0.5, 0.5] }: ElementWithCoordinate) {
        this._elements.addItem(element);
        this._coordinates.addItem(coordinate);
        this.coordinates = this._coordinates.toJSON() as BasisSchema["coordinates"];
    }

    /**
     * Remove atom with a chemical element at coordinate either by passing the (element AND coordinate) OR id.
     */
    removeAtom({ element, coordinate, id }: ElementWithCoordinate) {
        if (element && coordinate) {
            const coordinateId = this._coordinates.getElementIdByValue(coordinate) || -1;
            this._elements.removeItem(coordinateId, id);
            this._coordinates.removeItem(coordinateId, id);
        }
    }

    /**
     * Unique names (symbols) of the chemical elements basis. E.g. `['Si', 'Li']`
     */
    get uniqueElements(): AtomicElementValue[] {
        return uniq(this._elements.values);
    }

    /**
     * Returns unique chemical elements with their count sorted by electronegativity.
     * `{ "Fe": 4.0, "O": 8.0, "Li": 2.0}`.
     */
    get uniqueElementCountsSortedByElectronegativity() {
        return chain(this.elements)
            .sortBy("value")
            .sortBy((x) => getElectronegativity(x.value))
            .countBy((element) => element.value)
            .value();
    }

    /**
     * Returns chemical elements with their count wrt their original order in the basis.
     * Note: entries for the same element separated by another element are considered separately.
     * [{"count":1, "value":"Zr"}, {"count":23, "value":"H"}, {"count":11, "value":"Zr"}, {"count":1, "value":"H"}]
     */
    get elementCounts(): ElementCount[] {
        const elementCounts: ElementCount[] = [];
        this.elements.forEach((element, index) => {
            const previousElement = this.elements[index - 1];
            if (previousElement && previousElement.value === element.value) {
                const previousElementCount = elementCounts[elementCounts.length - 1];
                previousElementCount.count += 1;
            } else {
                elementCounts.push({
                    count: 1,
                    value: element.value,
                });
            }
        });
        return elementCounts;
    }

    /**
     * Reduced formula in IUPAC format. E.g., Na2SO4
     */
    get formula(): string {
        const counts = this.uniqueElementCountsSortedByElectronegativity;
        const countsValues = values(counts);
        const gcd = countsValues.length > 1 ? Utils.math.gcd(...countsValues) : countsValues[0];

        return toPairs(counts)
            .map(([element, count]) => element + (count / gcd === 1 ? "" : count / gcd))
            .reduce((acc, part) => acc + part, "");
    }

    /**
     * Returns the unit cell formula as object `{ "Fe": 4.0, "O": 8.0, "Li": 2.0}`
     */
    get unitCellFormula(): string {
        const counts = this.uniqueElementCountsSortedByElectronegativity;
        return toPairs(counts)
            .map(([element, count]) => element + (count === 1 ? "" : count))
            .reduce((acc, part) => acc + part, "");
    }

    /**
     * Returns a nested array with elements and their corresponding coordinates
     * @example Output: [ ["Si", [0,0,0]], ["Si", [0.5,0.5,0.5]] ]
     */
    get elementsAndCoordinatesArray(): [AtomicElementValue, AtomicCoordinateValue][] {
        return this._elements.values.map((element, idx) => {
            const coordinate = this.getCoordinateValueByIndex(idx);
            return [element, coordinate];
        });
    }

    /**
     * Returns a nested array with elements and their corresponding coordinates with labels
     * @example Output: [ ["Si", [0,0,0], ['1']], ["Si", [0.5,0.5,0.5]] , ['2']]
     */
    get elementsAndCoordinatesAndLabelsArray(): [
        AtomicElementValue,
        AtomicCoordinateValue,
        AtomicLabelValue,
    ][] {
        return this._elements.values.map((element, idx) => {
            const coordinate = this.getCoordinateValueByIndex(idx);
            const atomicLabel = this.atomicLabelsArray[idx];
            return [element, coordinate, atomicLabel];
        });
    }

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
    getAsSortedString(): string {
        const clsInstance = this.clone();
        clsInstance.toStandardRepresentation();
        const standardRep = clsInstance.elementsAndCoordinatesAndLabelsArray.map((entry) => {
            const element = entry[0];
            const coordinate = entry[1];
            const atomicLabel = entry[2];
            const toleratedCoordinate = coordinate.map((x) => Utils.math.roundCustom(x, HASH_TOLERANCE));
            return `${element}${atomicLabel} ${toleratedCoordinate.join()}`;
        });
        return `${standardRep.sort().join(";")};`;
    }

    /**
     * Returns a string for hash calculation (in crystal units)
     */
    get hashString(): string {
        const originallyInCartesianUnits = this.isInCartesianUnits;

        this.toCrystal();
        const hashString = this.getAsSortedString();

        // preserve the original state
        if (originallyInCartesianUnits) this.toCartesian();

        return hashString;
    }

    /* Returns array of atomic labels E.g., ["1", "2", "", ""] */
    get atomicLabelsArray(): string[] {
        const labelsArray = Array.from({ length: this.elements.length }, (_) => "");
        // https://dev.to/maafaishal/benchmarking-for-while-forof-and-arrayforeach-using-performancenow-1jjg
        if (this.labels?.length) {
            for (let i = 0; i < this.labels.length; i++) {
                // @ts-ignore
                labelsArray[this.labels[i].id] = this.labels[i].value.toString();
            }
        }
        return labelsArray;
    }

    /* Returns array of elements with labels E.g., ["Fe1", "Fe2", "O", "O"] */
    get elementsWithLabelsArray(): string[] {
        return this.elements.map((element, i) => {
            const label = this.labels?.[i]?.value || "";
            return `${element.value}${label}`;
        });
    }

    /**
     * Returns an array of strings with chemical elements and their atomic positions.
     * E.g., ``` ['Si 0 0 0', 'Li 0.5 0.5 0.5']```
     */
    get atomicPositions(): string[] {
        return this.elementsAndCoordinatesAndLabelsArray.map((entry, idx) => {
            const element = entry[0];
            const coordinate = entry[1];
            const atomicLabel = this.atomicLabelsArray[idx];
            return `${element}${atomicLabel} ${coordinate}`;
        });
    }

    /**
     * @summary Returns number of atoms in material
     */
    get nAtoms(): number {
        return this._elements.values.length;
    }

    // helpers

    /**
     * @summary Returns true if bases are equal, otherwise - false.
     * @param anotherBasisClsInstance {Basis} Another Basis.
     */
    isEqualTo(anotherBasisClsInstance: Basis): boolean {
        return this.hashString === anotherBasisClsInstance.hashString;
    }

    /**
     * @summary Returns true if basis cells are equal, otherwise - false.
     * @param anotherBasisClsInstance {Basis} Another Basis.
     */
    hasEquivalentCellTo(anotherBasisClsInstance: Basis): boolean {
        return !this.cell.vectorArrays
            .map((vector, idx) => {
                return Utils.math.vEqualWithTolerance(
                    vector,
                    anotherBasisClsInstance.cell.vectorArrays[idx],
                );
            })
            .some((x) => !x);
    }

    /**
     * @summary Returns the minimum cubic lattice size for a non-periodic structure.
     * Single-atom structures use the element atomic radius floored at defaultMinimumLatticeSize.
     * Multi-atom structures scale the maximum pairwise distance by 3 when W=min/max pairwise distance
     * is ~1 (diatomic), otherwise by 2.
     */
    getMinimumLatticeSize(
        defaultMinimumLatticeSize = defaultNonPeriodicMinimumLatticeSize,
    ): number {
        if (this._elements.values.length === 1) {
            const elementSymbol = this._elements.getElementValueByIndex(0);
            const atomicRadius = getElementAtomicRadius(elementSymbol);
            return Math.max(defaultMinimumLatticeSize, atomicRadius);
        }
        const maxDistance = this.maxPairwiseDistance;
        const minDistance = this.minPairwiseDistance;
        const widthRatio = maxDistance > 0 ? minDistance / maxDistance : 1;
        const latticeScalingFactor = Utils.math.almostEqual(widthRatio, 1)
            ? diatomicLatticePaddingFactor
            : molecularLatticePaddingFactor;
        const moleculeLatticeSize = maxDistance * latticeScalingFactor;
        return Math.max(defaultMinimumLatticeSize, moleculeLatticeSize);
    }

    /**
     * @summary function returns an array of overlapping atoms within specified tolerance.
     */
    getOverlappingAtoms(): Overlap[] {
        // to simplify calculations, convert to cartesian coordinates
        this.toCartesian();
        const { coordinates, elements } = this;
        const overlaps: Overlap[] = [];
        // temporary value for overlap approximation, where atoms most certainly can't be located
        const overlapCoefficient = 0.75;

        coordinates.forEach((entry1, i) => {
            for (let j = i + 1; j < coordinates.length; j++) {
                const entry2 = coordinates[j];
                const el1 = elements[i].value;
                const el2 = elements[j].value;

                const tolerance =
                    overlapCoefficient *
                    (getElementAtomicRadius(el1) + getElementAtomicRadius(el2)); // in angstroms

                // @ts-ignore
                const distance = Utils.math.vDist(entry1.value, entry2.value) as number;
                if (distance < tolerance) {
                    overlaps.push({
                        id1: i,
                        id2: j,
                        element1: el1,
                        element2: el2,
                    });
                }
            }
        });

        this.toCrystal();
        return overlaps;
    }

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
    get maxPairwiseDistance(): number {
        return this.getPairwiseDistanceExtremum("max");
    }

    get minPairwiseDistance(): number {
        return this.getPairwiseDistanceExtremum("min");
    }

    getPairwiseDistanceExtremum(extremum: "max" | "min"): number {
        const originalUnits = this.units;
        this.toCartesian();
        let resultDistance = extremum === "max" ? 0 : Infinity;
        if (this._elements.values.length >= 2) {
            for (let i = 0; i < this._elements.values.length; i++) {
                for (let j = i + 1; j < this._elements.values.length; j++) {
                    const distance = Utils.math.vDist(
                        this._coordinates.getElementValueByIndex(i) as Coordinate3DSchema,
                        this._coordinates.getElementValueByIndex(j) as Coordinate3DSchema,
                    );
                    if (!distance) continue;
                    if (extremum === "max" && distance > resultDistance) {
                        resultDistance = distance;
                    }
                    if (extremum === "min" && distance < resultDistance) {
                        resultDistance = distance;
                    }
                }
            }
        }
        if (originalUnits !== ATOMIC_COORD_UNITS.cartesian) this.toCrystal();
        return extremum === "min" && resultDistance === Infinity ? 0 : resultDistance;
    }

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
    get centerOfCoordinatesPoint(): AtomicCoordinateValue {
        return this._coordinates.getCenterPoint();
    }

    /**
     * @summary Function translates coordinates by the vector passed as an argument.
     */
    translateByVector(translationVector: Vector3DSchema) {
        this._coordinates.translateByVector(translationVector);
    }
}
