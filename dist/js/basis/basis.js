"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Basis = void 0;
// @ts-ignore
const periodic_table_js_1 = require("@exabyte-io/periodic-table.js");
const entity_1 = require("@mat3ra/code/dist/js/entity");
const utils_1 = require("@mat3ra/utils");
const lodash_1 = require("lodash");
const cell_1 = require("../cell/cell");
const constants_1 = require("../constants");
const lattice_1 = require("../lattice/lattice");
const coordinates_1 = require("./coordinates");
const elements_1 = require("./elements");
const labels_1 = require("./labels");
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
class Basis extends entity_1.InMemoryEntity {
    static _convertValuesToConfig({ elements = [], coordinates = [], units = constants_1.ATOMIC_COORD_UNITS.crystal, cell = new cell_1.Cell(), labels = [], }) {
        const elementsArrayWithIdsJSON = elements_1.Elements.fromValues(elements).toJSON();
        const coordinatesArrayWithIdsJSON = coordinates_1.Coordinates.fromValues(coordinates).toJSON();
        const labelsArrayWithIdsJSON = labels_1.Labels.fromValues(labels).toJSON();
        return {
            elements: elementsArrayWithIdsJSON,
            coordinates: coordinatesArrayWithIdsJSON,
            units,
            cell,
            labels: labelsArrayWithIdsJSON,
        };
    }
    static fromElementsAndCoordinates({ elements = [], coordinates = [], units = constants_1.ATOMIC_COORD_UNITS.crystal, cell = new cell_1.Cell(), labels = [], }) {
        return new Basis(Basis._convertValuesToConfig({
            elements,
            coordinates,
            units,
            cell,
            labels,
        }));
    }
    constructor(config = Basis.defaultConfig) {
        super(config);
        const { elements, coordinates, units, labels } = config;
        this.cell = new cell_1.Cell(config.cell);
        this.units = units || constants_1.ATOMIC_COORD_UNITS.crystal;
        this._elements = elements_1.Elements.fromObjects(elements);
        this._coordinates = coordinates_1.Coordinates.fromObjects(coordinates);
        this._labels = labels_1.Labels.fromObjects(labels || []);
    }
    get elements() {
        return this._elements.toJSON();
    }
    set elements(elements) {
        this._elements = elements_1.Elements.fromObjects(elements);
    }
    get coordinates() {
        return this._coordinates.toJSON();
    }
    set coordinates(coordinates) {
        this._coordinates = coordinates_1.Coordinates.fromObjects(coordinates);
    }
    get labels() {
        return this._labels.toJSON();
    }
    set labels(labels) {
        this._labels = labels_1.Labels.fromObjects(labels || []);
    }
    toJSON(exclude = ["cell"]) {
        var _a;
        return {
            ...super.toJSON(exclude),
            elements: this.elements,
            coordinates: this.coordinates,
            units: this.units,
            ...(((_a = this.labels) === null || _a === void 0 ? void 0 : _a.length) ? { labels: this.labels } : {}),
        };
    }
    clone() {
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
    get elementsArray() {
        return this._elements.toJSON();
    }
    getElementsAsObject() {
        return this.elements;
    }
    get coordinatesAsArray() {
        return this._coordinates.values;
    }
    get isInCartesianUnits() {
        return this.units === constants_1.ATOMIC_COORD_UNITS.cartesian;
    }
    get isInCrystalUnits() {
        return this.units === constants_1.ATOMIC_COORD_UNITS.crystal;
    }
    toCartesian() {
        if (this.isInCartesianUnits)
            return this;
        this._coordinates.mapArrayInPlace((point) => this.cell.convertPointToCartesian(point));
        this.units = constants_1.ATOMIC_COORD_UNITS.cartesian;
        return this;
    }
    toCrystal() {
        if (this.isInCrystalUnits)
            return this;
        this._coordinates.mapArrayInPlace((point) => this.cell.convertPointToCrystal(point));
        this.units = constants_1.ATOMIC_COORD_UNITS.crystal;
        return this;
    }
    getElementByIndex(idx) {
        return this._elements.getElementValueByIndex(idx);
    }
    getElementById(id) {
        const result = this._elements.getElementValueById(id);
        if (result) {
            return result;
        }
        throw new Error(`Element with index ${id} not found`);
    }
    getCoordinateValueByIndex(idx) {
        const value = this._coordinates.getElementValueByIndex(idx);
        if (value) {
            return value;
        }
        throw new Error(`Coordinate with index ${idx} not found`);
    }
    getCoordinateValueById(id) {
        const coordinate = this._coordinates.getElementValueById(id);
        if (coordinate) {
            return coordinate;
        }
        throw new Error(`Coordinate with index ${id} not found`);
    }
    toStandardRepresentation() {
        this.toCrystal();
        this._coordinates.mapArrayInPlace((point) => point.map((x) => utils_1.Utils.math.mod(x)));
    }
    /** A representation where all coordinates are within 0 and 1 in crystal units */
    get standardRepresentation() {
        const originalIsInCartesianUnits = this.isInCartesianUnits;
        this.toStandardRepresentation();
        const result = this.toJSON();
        if (originalIsInCartesianUnits)
            this.toCartesian();
        return result;
    }
    /**
     * Add atom with a chemical element at coordinate.
     */
    addAtom({ element = "Si", coordinate = [0.5, 0.5, 0.5] }) {
        this._elements.addItem(element);
        this._coordinates.addItem(coordinate);
        this.coordinates = this._coordinates.toJSON();
    }
    /**
     * Remove atom with a chemical element at coordinate either by passing the (element AND coordinate) OR id.
     */
    removeAtom({ element, coordinate, id }) {
        if (element && coordinate) {
            const coordinateId = this._coordinates.getElementIdByValue(coordinate) || -1;
            this._elements.removeItem(coordinateId, id);
            this._coordinates.removeItem(coordinateId, id);
        }
    }
    /**
     * Unique names (symbols) of the chemical elements basis. E.g. `['Si', 'Li']`
     */
    get uniqueElements() {
        return (0, lodash_1.uniq)(this._elements.values);
    }
    /**
     * Returns unique chemical elements with their count sorted by electronegativity.
     * `{ "Fe": 4.0, "O": 8.0, "Li": 2.0}`.
     */
    get uniqueElementCountsSortedByElectronegativity() {
        return (0, lodash_1.chain)(this.elements)
            .sortBy("value")
            .sortBy((x) => (0, periodic_table_js_1.getElectronegativity)(x.value))
            .countBy((element) => element.value)
            .value();
    }
    /**
     * Returns chemical elements with their count wrt their original order in the basis.
     * Note: entries for the same element separated by another element are considered separately.
     * [{"count":1, "value":"Zr"}, {"count":23, "value":"H"}, {"count":11, "value":"Zr"}, {"count":1, "value":"H"}]
     */
    get elementCounts() {
        const elementCounts = [];
        this.elements.forEach((element, index) => {
            const previousElement = this.elements[index - 1];
            if (previousElement && previousElement.value === element.value) {
                const previousElementCount = elementCounts[elementCounts.length - 1];
                previousElementCount.count += 1;
            }
            else {
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
    get formula() {
        const counts = this.uniqueElementCountsSortedByElectronegativity;
        const countsValues = (0, lodash_1.values)(counts);
        const gcd = countsValues.length > 1 ? utils_1.Utils.math.gcd(...countsValues) : countsValues[0];
        return (0, lodash_1.toPairs)(counts)
            .map(([element, count]) => element + (count / gcd === 1 ? "" : count / gcd))
            .reduce((acc, part) => acc + part, "");
    }
    /**
     * Returns the unit cell formula as object `{ "Fe": 4.0, "O": 8.0, "Li": 2.0}`
     */
    get unitCellFormula() {
        const counts = this.uniqueElementCountsSortedByElectronegativity;
        return (0, lodash_1.toPairs)(counts)
            .map(([element, count]) => element + (count === 1 ? "" : count))
            .reduce((acc, part) => acc + part, "");
    }
    /**
     * Returns a nested array with elements and their corresponding coordinates
     * @example Output: [ ["Si", [0,0,0]], ["Si", [0.5,0.5,0.5]] ]
     */
    get elementsAndCoordinatesArray() {
        return this._elements.values.map((element, idx) => {
            const coordinate = this.getCoordinateValueByIndex(idx);
            return [element, coordinate];
        });
    }
    /**
     * Returns a nested array with elements and their corresponding coordinates with labels
     * @example Output: [ ["Si", [0,0,0], ['1']], ["Si", [0.5,0.5,0.5]] , ['2']]
     */
    get elementsAndCoordinatesAndLabelsArray() {
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
    getAsSortedString() {
        const clsInstance = this.clone();
        clsInstance.toStandardRepresentation();
        const standardRep = clsInstance.elementsAndCoordinatesAndLabelsArray.map((entry) => {
            const element = entry[0];
            const coordinate = entry[1];
            const atomicLabel = entry[2];
            const toleratedCoordinate = coordinate.map((x) => utils_1.Utils.math.roundCustom(x, constants_1.HASH_TOLERANCE));
            return `${element}${atomicLabel} ${toleratedCoordinate.join()}`;
        });
        return `${standardRep.sort().join(";")};`;
    }
    /**
     * Returns a string for hash calculation (in crystal units)
     */
    get hashString() {
        const originallyInCartesianUnits = this.isInCartesianUnits;
        this.toCrystal();
        const hashString = this.getAsSortedString();
        // preserve the original state
        if (originallyInCartesianUnits)
            this.toCartesian();
        return hashString;
    }
    /* Returns array of atomic labels E.g., ["1", "2", "", ""] */
    get atomicLabelsArray() {
        var _a;
        const labelsArray = Array.from({ length: this.elements.length }, (_) => "");
        // https://dev.to/maafaishal/benchmarking-for-while-forof-and-arrayforeach-using-performancenow-1jjg
        if ((_a = this.labels) === null || _a === void 0 ? void 0 : _a.length) {
            for (let i = 0; i < this.labels.length; i++) {
                // @ts-ignore
                labelsArray[this.labels[i].id] = this.labels[i].value.toString();
            }
        }
        return labelsArray;
    }
    /* Returns array of elements with labels E.g., ["Fe1", "Fe2", "O", "O"] */
    get elementsWithLabelsArray() {
        return this.elements.map((element, i) => {
            var _a, _b;
            const label = ((_b = (_a = this.labels) === null || _a === void 0 ? void 0 : _a[i]) === null || _b === void 0 ? void 0 : _b.value) || "";
            return `${element.value}${label}`;
        });
    }
    /**
     * Returns an array of strings with chemical elements and their atomic positions.
     * E.g., ``` ['Si 0 0 0', 'Li 0.5 0.5 0.5']```
     */
    get atomicPositions() {
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
    get nAtoms() {
        return this._elements.values.length;
    }
    // helpers
    /**
     * @summary Returns true if bases are equal, otherwise - false.
     * @param anotherBasisClsInstance {Basis} Another Basis.
     */
    isEqualTo(anotherBasisClsInstance) {
        return this.hashString === anotherBasisClsInstance.hashString;
    }
    /**
     * @summary Returns true if basis cells are equal, otherwise - false.
     * @param anotherBasisClsInstance {Basis} Another Basis.
     */
    hasEquivalentCellTo(anotherBasisClsInstance) {
        return !this.cell.vectorArrays
            .map((vector, idx) => {
            return utils_1.Utils.math.vEqualWithTolerance(vector, anotherBasisClsInstance.cell.vectorArrays[idx]);
        })
            .some((x) => !x);
    }
    /**
     * @summary Returns the minimum cubic lattice size for a non-periodic structure.
     * Single-atom structures use the element atomic radius floored at defaultMinimumLatticeSize.
     * Multi-atom structures scale the maximum pairwise distance by 3 when W=min/max pairwise distance
     * is ~1 (diatomic), otherwise by 2.
     */
    getMinimumLatticeSize(defaultMinimumLatticeSize = lattice_1.defaultNonPeriodicMinimumLatticeSize) {
        if (this._elements.values.length === 1) {
            const elementSymbol = this._elements.getElementValueByIndex(0);
            const atomicRadius = (0, periodic_table_js_1.getElementAtomicRadius)(elementSymbol);
            return Math.max(defaultMinimumLatticeSize, atomicRadius);
        }
        const maxDistance = this.maxPairwiseDistance;
        const minDistance = this.minPairwiseDistance;
        const widthRatio = maxDistance > 0 ? minDistance / maxDistance : 1;
        const latticeScalingFactor = utils_1.Utils.math.almostEqual(widthRatio, 1)
            ? lattice_1.diatomicLatticePaddingFactor
            : lattice_1.molecularLatticePaddingFactor;
        const moleculeLatticeSize = maxDistance * latticeScalingFactor;
        return Math.max(defaultMinimumLatticeSize, moleculeLatticeSize);
    }
    /**
     * @summary function returns an array of overlapping atoms within specified tolerance.
     */
    getOverlappingAtoms() {
        // to simplify calculations, convert to cartesian coordinates
        this.toCartesian();
        const { coordinates, elements } = this;
        const overlaps = [];
        // temporary value for overlap approximation, where atoms most certainly can't be located
        const overlapCoefficient = 0.75;
        coordinates.forEach((entry1, i) => {
            for (let j = i + 1; j < coordinates.length; j++) {
                const entry2 = coordinates[j];
                const el1 = elements[i].value;
                const el2 = elements[j].value;
                const tolerance = overlapCoefficient *
                    ((0, periodic_table_js_1.getElementAtomicRadius)(el1) + (0, periodic_table_js_1.getElementAtomicRadius)(el2)); // in angstroms
                // @ts-ignore
                const distance = utils_1.Utils.math.vDist(entry1.value, entry2.value);
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
    get maxPairwiseDistance() {
        return this.getPairwiseDistanceExtremum("max");
    }
    get minPairwiseDistance() {
        return this.getPairwiseDistanceExtremum("min");
    }
    getPairwiseDistanceExtremum(extremum) {
        const originalUnits = this.units;
        this.toCartesian();
        let resultDistance = extremum === "max" ? 0 : Infinity;
        if (this._elements.values.length >= 2) {
            for (let i = 0; i < this._elements.values.length; i++) {
                for (let j = i + 1; j < this._elements.values.length; j++) {
                    const distance = utils_1.Utils.math.vDist(this._coordinates.getElementValueByIndex(i), this._coordinates.getElementValueByIndex(j));
                    if (!distance)
                        continue;
                    if (extremum === "max" && distance > resultDistance) {
                        resultDistance = distance;
                    }
                    if (extremum === "min" && distance < resultDistance) {
                        resultDistance = distance;
                    }
                }
            }
        }
        if (originalUnits !== constants_1.ATOMIC_COORD_UNITS.cartesian)
            this.toCrystal();
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
    get centerOfCoordinatesPoint() {
        return this._coordinates.getCenterPoint();
    }
    /**
     * @summary Function translates coordinates by the vector passed as an argument.
     */
    translateByVector(translationVector) {
        this._coordinates.translateByVector(translationVector);
    }
}
exports.Basis = Basis;
Basis.defaultConfig = DEFAULT_BASIS_CONFIG;
