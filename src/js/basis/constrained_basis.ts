import { ArrayWithIds } from "@mat3ra/code";
import { AtomicConstraintsSchema, BasisConstrainedSchema } from "@mat3ra/esse/dist/js/types";

import { Cell } from "../cell/cell";
import { AtomicConstraints, AtomicConstraintValue, Constraint } from "../constraints/constraints";
import { Basis, ElementsAndCoordinatesConfig } from "./basis";
import { AtomicCoordinateValue, Coordinate } from "./coordinates";
import { AtomicElementValue } from "./elements";
import { ElementWithLabel } from "./helpers";
import { Labels } from "./labels";

export interface ConstrainedBasisConfig extends BasisConstrainedSchema {
    cell?: Cell;
    isEmpty?: boolean;
}

export interface ElementsCoordinatesAndConstraintsConfig extends ElementsAndCoordinatesConfig {
    constraints: AtomicConstraintValue[];
}

/**
 * @summary Extension of the Basis class able to deal with atomic constraints.
 * @extends Basis
 */
export class ConstrainedBasis extends Basis<ConstrainedBasisConfig> {
    private _constraints: AtomicConstraints;

    _labels: Labels;

    _startingMagnetization: ArrayWithIds<number>;

    constructor(config: ConstrainedBasisConfig) {
        super(config);
        this._constraints = AtomicConstraints.fromObjects(config.constraints ?? []); // `constraints` is an Array with ids
        this._labels = Labels.fromObjects(config.labels || []);
        this._startingMagnetization = ArrayWithIds.fromObjects(config.startingMagnetization || []);
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

    get labels(): ConstrainedBasisConfig["labels"] {
        return this._labels.toJSON() as ConstrainedBasisConfig["labels"];
    }

    set labels(labels: ConstrainedBasisConfig["labels"]) {
        this._labels = Labels.fromObjects(labels || []);
    }

    get startingMagnetization(): ConstrainedBasisConfig["startingMagnetization"] {
        return this._startingMagnetization.toJSON() as ConstrainedBasisConfig["startingMagnetization"];
    }

    set startingMagnetization(
        startingMagnetization: ConstrainedBasisConfig["startingMagnetization"],
    ) {
        this._startingMagnetization = ArrayWithIds.fromObjects(startingMagnetization || []);
    }

    override toJSON(exclude: (keyof ConstrainedBasisConfig)[] = ["cell"]): ConstrainedBasisConfig {
        return {
            ...super.toJSON(exclude as (keyof ConstrainedBasisConfig)[]),
            constraints: this.constraints,
            ...(this.labels?.length ? { labels: this.labels } : {}),
            ...(this.startingMagnetization?.length
                ? { startingMagnetization: this.startingMagnetization }
                : {}),
        };
    }

    /* Returns array of atomic labels by atom id E.g., ["1", "2", "", ""] */
    get atomicLabelsArray(): string[] {
        const { ids, values } = this._labels;
        const labelById = new Map(ids.map((id, index) => [id, `${values[index]}`] as const));
        return this._elements.ids.map((id) => labelById.get(id) ?? "");
    }

    /* Returns array of starting magnetization by atom id E.g., [0.5, -0.5, 0, 0] */
    get startingMagnetizationArray(): number[] {
        const { ids, values } = this._startingMagnetization;
        const valueById = new Map(ids.map((id, index) => [id, values[index]] as const));
        return this._elements.ids.map((id) => valueById.get(id) ?? 0);
    }

    /* Returns array of elements with labels E.g., ["Fe1", "Fe2", "O", "O"] */
    get elementsWithLabelsArray(): string[] {
        return this.atomicLabelsArray.map(
            (label, index) => `${this.getElementByIndex(index)}${label}`,
        );
    }

    /**
     * Returns an array of strings with chemical elements and their atomic positions.
     * E.g., ``` ['Si 0 0 0', 'Li 0.5 0.5 0.5']```
     */
    get atomicPositions(): string[] {
        return this.elementsWithLabelsArray.map(
            (elementWithLabel, index) =>
                `${elementWithLabel} ${this.getCoordinateValueByIndex(index)}`,
        );
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
        string,
        AtomicCoordinateValue,
        AtomicConstraintValue,
    ][] {
        return this._elements.values.map((element: AtomicElementValue, idx: number) => {
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
        this.labels = [];
        this.startingMagnetization = [];
    }
}
