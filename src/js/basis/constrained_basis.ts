import { AtomicConstraintsSchema } from "@mat3ra/esse/dist/js/types";

import { AtomicConstraints, AtomicConstraintValue, Constraint } from "../constraints/constraints";
import { Basis, BasisConfig, ElementsAndCoordinatesConfig } from "./basis";
import { AtomicCoordinateValue, Coordinate } from "./coordinates";
import { AtomicElementValue } from "./elements";
import { ElementWithLabel } from "./helpers";
import { AtomicLabelValue } from "./labels";

export interface ConstrainedBasisConfig extends BasisConfig {
    constraints: AtomicConstraintsSchema;
}

export interface ElementsCoordinatesAndConstraintsConfig extends ElementsAndCoordinatesConfig {
    constraints: AtomicConstraintValue[];
}

/**
 * @summary Extension of the Basis class able to deal with atomic constraints.
 * @extends Basis
 */
export class ConstrainedBasis extends Basis {
    private _constraints: AtomicConstraints;

    constructor(config: ConstrainedBasisConfig) {
        super(config);
        this._constraints = AtomicConstraints.fromObjects(config.constraints); // `constraints` is an Array with ids
    }

    static fromElementsCoordinatesAndConstraints(
        config: ElementsCoordinatesAndConstraintsConfig,
    ): ConstrainedBasis {
        const basisConfig = this._convertValuesToConfig(config);
        const constraints = AtomicConstraints.fromValues(config.constraints);
        return new this({
            ...basisConfig,
            constraints: constraints.toJSON() as AtomicConstraintsSchema,
        });
    }

    get constraints() {
        return this._constraints.toJSON() as AtomicConstraintsSchema;
    }

    set constraints(constraints: AtomicConstraintsSchema) {
        this._constraints = AtomicConstraints.fromObjects(constraints);
    }

    get AtomicConstraints() {
        return AtomicConstraints.fromObjects(this.constraints);
    }

    override toJSON(): ConstrainedBasisConfig {
        return {
            ...super.toJSON(),
            constraints: this.constraints,
        };
    }

    getConstraintByIndex(idx: number): AtomicConstraintValue {
        return this._constraints.getElementValueByIndex(idx) || [true, true, true];
    }

    getConstraintById(id: number): AtomicConstraintValue {
        return this._constraints.getElementValueById(id) || [true, true, true];
    }

    /**
     * Helper function returning a nested array with [element, coordinates, constraints] as elements
     */
    get elementsCoordinatesConstraintsArray(): [
        AtomicElementValue,
        AtomicLabelValue,
        AtomicCoordinateValue,
        AtomicConstraintValue,
    ][] {
        return this._elements.values.map((element: any, idx: number) => {
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
    getAtomicPositionsWithConstraintsAsStrings(
        coordinatePrintFormat?: string,
        precision?: number,
    ): string[] {
        const omitConstraints = this._constraints.areUnconstrained;
        return this.elementsCoordinatesConstraintsArray.map(
            ([element, label, coordinate, constraint]) => {
                const _elementWithLabel = new ElementWithLabel({ element, label });
                const _coordinate = Coordinate.fromValueAndId(coordinate);
                const _constraint = Constraint.fromValueAndId(constraint);

                return [
                    _elementWithLabel.prettyPrint(),
                    _coordinate.prettyPrint(coordinatePrintFormat, precision),
                    omitConstraints ? "" : _constraint.prettyPrint(),
                ].join(" ");
            },
        );
    }

    removeAllAtoms() {
        super.removeAllAtoms();
        this.constraints = [];
    }
}
