"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConstrainedBasis = void 0;
const constraints_1 = require("../constraints/constraints");
const basis_1 = require("./basis");
const coordinates_1 = require("./coordinates");
const helpers_1 = require("./helpers");
/**
 * @summary Extension of the Basis class able to deal with atomic constraints.
 * @extends Basis
 */
class ConstrainedBasis extends basis_1.Basis {
    constructor(config) {
        super(config);
        this._constraints = constraints_1.AtomicConstraints.fromObjects(config.constraints); // `constraints` is an Array with ids
    }
    static fromElementsCoordinatesAndConstraints(config) {
        const basisConfig = this._convertValuesToConfig(config);
        const constraints = constraints_1.AtomicConstraints.fromValues(config.constraints);
        return new this({
            ...basisConfig,
            constraints: constraints.toJSON(),
        });
    }
    get constraints() {
        return this._constraints.toJSON();
    }
    set constraints(constraints) {
        this._constraints = constraints_1.AtomicConstraints.fromObjects(constraints);
    }
    get AtomicConstraints() {
        return constraints_1.AtomicConstraints.fromObjects(this.constraints);
    }
    toJSON() {
        return {
            ...super.toJSON(),
            constraints: this.constraints,
        };
    }
    getConstraintByIndex(idx) {
        return this._constraints.getElementValueByIndex(idx) || [true, true, true];
    }
    getConstraintById(id) {
        return this._constraints.getElementValueById(id) || [true, true, true];
    }
    /**
     * Helper function returning a nested array with [element, coordinates, constraints] as elements
     */
    get elementsCoordinatesConstraintsArray() {
        return this._elements.values.map((element, idx) => {
            const coordinate = this.getCoordinateValueByIndex(idx);
            const constraint = this.getConstraintByIndex(idx);
            const label = this.atomicLabelsArray[idx];
            return [element, label, coordinate, constraint];
        });
    }
    /**
     * Returns an array with atomic positions (with constraints) per atom stored as strings.
     * E.g., ``` ['Si  0 0 0  0 1 0', 'Li  0.5 0.5 0.5  1 0 1']```
     */
    getAtomicPositionsWithConstraintsAsStrings(coordinatePrintFormat, precision) {
        const omitConstraints = this._constraints.areUnconstrained;
        return this.elementsCoordinatesConstraintsArray.map(([element, label, coordinate, constraint]) => {
            const _elementWithLabel = new helpers_1.ElementWithLabel({ element, label });
            const _coordinate = coordinates_1.Coordinate.fromValueAndId(coordinate);
            const _constraint = constraints_1.Constraint.fromValueAndId(constraint);
            return [
                _elementWithLabel.prettyPrint(),
                _coordinate.prettyPrint(coordinatePrintFormat, precision),
                omitConstraints ? "" : _constraint.prettyPrint(),
            ].join(" ");
        });
    }
    removeAllAtoms() {
        super.removeAllAtoms();
        this.constraints = [];
    }
}
exports.ConstrainedBasis = ConstrainedBasis;
