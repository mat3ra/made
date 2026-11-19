import {
    AtomicConstraintsSchema,
    AtomicLabelsSchema,
    BasisConstrainedSchema,
} from "@mat3ra/esse/dist/js/types";
import s from "underscore.string";

import { Cell } from "../cell/cell";
import { AtomicConstraints, AtomicConstraintValue, Constraint } from "../constraints/constraints";
import { Basis, ElementsAndCoordinatesConfig } from "./basis";
import { AtomicCoordinateValue, Coordinate } from "./coordinates";
import { AtomicElementValue } from "./elements";

export interface ConstrainedBasisConfig extends BasisConstrainedSchema {
    cell?: Cell;
    isEmpty?: boolean;
    labels?: AtomicLabelsSchema["values"];
}

export interface ElementsCoordinatesAndConstraintsConfig extends ElementsAndCoordinatesConfig {
    constraints: AtomicConstraintValue[];
}

/**
 * @summary Extension of the Basis class holding per-atom constraints and labels.
 * @extends Basis
 */
export class ConstrainedBasis extends Basis<ConstrainedBasisConfig> {
    static readonly PER_ATOM_KEYS = ["constraints", "labels"] as const;

    private _constraints: AtomicConstraints;

    labels: AtomicLabelsSchema["values"];

    constructor(config: ConstrainedBasisConfig) {
        super(config);
        this._constraints = AtomicConstraints.fromObjects(config.constraints ?? []); // `constraints` is an Array with ids
        this.labels = config.labels ?? [];
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

    override toJSON(exclude: (keyof ConstrainedBasisConfig)[] = ["cell"]): ConstrainedBasisConfig {
        return {
            ...super.toJSON(exclude as (keyof ConstrainedBasisConfig)[]),
            ...Object.fromEntries(ConstrainedBasis.PER_ATOM_KEYS.map((key) => [key, this[key]])),
        };
    }

    /** Returns the value of each atom, in basis order, from per-atom entries keyed by atom id */
    valuesByAtom<T>(entries: { id: number; value: T }[]): (T | undefined)[] {
        const valueById = new Map(entries.map(({ id, value }) => [id, value]));
        return this._elements.ids.map((id) => valueById.get(id));
    }

    /** Returns array of atomic labels by atom id E.g., ["1", "2", "", ""] */
    get atomicLabelsArray(): string[] {
        return this.valuesByAtom(this.labels).map((label) => label?.toString() ?? "");
    }

    /** Returns array of elements with labels E.g., ["Fe1", "Fe2", "O", "O"] */
    get elementsWithLabelsArray(): string[] {
        return this.atomicLabelsArray.map(
            (label, index) => `${this.getElementByIndex(index)}${label ?? ""}`,
        );
    }

    /**
     * Returns an array of strings with chemical elements and their atomic positions.
     * E.g., ``` ['Si 0 0 0', 'Li 0.5 0.5 0.5']```
     */
    get atomicPositions(): string[] {
        return this.elementsWithLabelsArray.map(
            (atomName, index) => `${atomName} ${this.getCoordinateValueByIndex(index)}`,
        );
    }

    getConstraintByIndex(idx: number): AtomicConstraintValue {
        return this._constraints.getElementValueByIndex(idx) || [true, true, true];
    }

    getConstraintById(id: number): AtomicConstraintValue {
        return this._constraints.getElementValueById(id) || [true, true, true];
    }

    /**
     * Helper function returning a nested array with [element, label, coordinates, constraints] as elements
     */
    get elementsCoordinatesConstraintsArray(): [
        AtomicElementValue,
        string,
        AtomicCoordinateValue,
        AtomicConstraintValue,
    ][] {
        const { atomicLabelsArray } = this;
        return this._elements.values.map((element: AtomicElementValue, idx: number) => {
            const coordinate = this.getCoordinateValueByIndex(idx);
            const constraint = this.getConstraintByIndex(idx);
            return [element, atomicLabelsArray[idx], coordinate, constraint];
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
        return this.elementsWithLabelsArray.map((atomName, index) => {
            const _coordinate = Coordinate.fromValueAndId(this.getCoordinateValueByIndex(index));
            const _constraint = Constraint.fromValueAndId(this.getConstraintByIndex(index));

            return [
                s.sprintf("%-3s", atomName),
                _coordinate.prettyPrint(coordinatePrintFormat, precision),
                omitConstraints ? "" : _constraint.prettyPrint(),
            ].join(" ");
        });
    }

    removeAllAtoms() {
        super.removeAllAtoms();
        ConstrainedBasis.PER_ATOM_KEYS.forEach((key) => {
            this[key] = [];
        });
    }
}
