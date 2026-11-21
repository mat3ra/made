import { ArrayWithIds } from "@mat3ra/code";
import { BasisWithAtomicPropertiesSchema } from "@mat3ra/esse/dist/js/types";

import { Cell } from "../cell/cell";
import { AtomicConstraints, AtomicConstraintValue, Constraint } from "../constraints/constraints";
import { AtomicProperties, ProtoPropertyEnum } from "./atomic_properties";
import { Basis, ElementsAndCoordinatesConfig } from "./basis";
import { AtomicCoordinateValue, Coordinate } from "./coordinates";
import { AtomicElementValue } from "./elements";
import { ElementWithLabel } from "./helpers";
import { AtomicLabelValue } from "./labels";

export interface BasisWithAtomicPropertiesConfig extends BasisWithAtomicPropertiesSchema {
    cell?: Cell;
    isEmpty?: boolean;
}

export interface ElementsCoordinatesAndConstraintsConfig extends ElementsAndCoordinatesConfig {
    constraints: AtomicConstraintValue[];
}

/**
 * @summary Extension of the Basis class able to deal with per-atom properties: constraints and labels.
 * @extends Basis
 */
export class BasisWithAtomicProperties extends Basis<BasisWithAtomicPropertiesConfig> {
    atomicProperties: AtomicProperties;

    constructor(config: BasisWithAtomicPropertiesConfig) {
        super(config);
        this.atomicProperties = new AtomicProperties(config.atomic_properties);
    }

    static fromElementsCoordinatesAndConstraints(
        config: ElementsCoordinatesAndConstraintsConfig,
    ): BasisWithAtomicProperties {
        const basis = new this(this._convertValuesToConfig(config));
        basis.atomicProperties.setByName(
            ProtoPropertyEnum.atomic_constraints,
            AtomicConstraints.fromValues(config.constraints),
        );
        return basis;
    }

    get AtomicConstraints() {
        return this.atomicProperties.getByName(ProtoPropertyEnum.atomic_constraints);
    }

    override toJSON(
        exclude: (keyof BasisWithAtomicPropertiesConfig)[] = ["cell"],
    ): BasisWithAtomicPropertiesConfig {
        return {
            ...super.toJSON(exclude as (keyof BasisWithAtomicPropertiesConfig)[]),
            atomic_properties: this.atomicProperties.toJSON(),
        };
    }

    getConstraintByIndex(idx: number): AtomicConstraintValue {
        return this.getConstraintById(this._elements.ids[idx]);
    }

    getConstraintById(id: number): AtomicConstraintValue {
        return this.AtomicConstraints.getElementValueById(id) || [true, true, true];
    }

    /**
     * Returns array of atomic labels E.g., [1, 2, undefined, undefined]
     */
    get atomicLabelsArray(): (AtomicLabelValue | undefined)[] {
        const labels = this.atomicProperties.getByName(ProtoPropertyEnum.atomic_labels);
        return this._elements.ids.map((id) => labels.getElementValueById(id));
    }

    /**
     * Returns array of elements with labels E.g., ["Fe1", "Fe2", "O", "O"]
     */
    get elementsWithLabelsArray(): string[] {
        return this.atomicLabelsArray.map(
            (label, index) => `${this.getElementByIndex(index)}${label ?? ""}`,
        );
    }

    override get siteNames(): string[] {
        return this.elementsWithLabelsArray;
    }

    /**
     * Helper function returning a nested array with [element, coordinates, constraints] as elements
     */
    get elementsCoordinatesConstraintsArray(): [
        AtomicElementValue,
        AtomicLabelValue | undefined,
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
        const omitConstraints = this.AtomicConstraints.areUnconstrained;
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

    override get perAtomValuesByName(): Record<string, ArrayWithIds<unknown>> {
        return { ...super.perAtomValuesByName, ...this.atomicProperties.propertyByName };
    }
}
