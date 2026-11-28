import { ArrayWithIds } from "@mat3ra/code";
import { BasisWithAtomicPropertiesSchema, ProtoPropertyEnum } from "@mat3ra/esse/dist/js/types";

import { Cell } from "../cell/cell";
import { AtomicConstraints, AtomicConstraintValue, Constraint } from "../constraints/constraints";
import { AtomicProperties } from "./atomic_properties";
import { Basis, ElementsAndCoordinatesConfig } from "./basis";
import { AtomicCoordinateValue, Coordinate } from "./coordinates";
import { AtomicElementValue } from "./elements";
import { ElementWithLabel } from "./helpers";
import { AtomicLabelValue, Labels } from "./labels";

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

    get constraints(): AtomicConstraints {
        return this.atomicProperties.getByName(ProtoPropertyEnum.atomic_constraints);
    }

    get labels(): Labels {
        return this.atomicProperties.getByName(ProtoPropertyEnum.atomic_labels);
    }

    override toJSON(
        exclude: (keyof BasisWithAtomicPropertiesConfig)[] = ["cell"],
    ): BasisWithAtomicPropertiesConfig {
        return {
            ...super.toJSON(exclude),
            atomic_properties: this.atomicProperties.toJSON(),
        };
    }

    getConstraintByIndex(idx: number): AtomicConstraintValue {
        return this.getConstraintById(this._elements.ids[idx]);
    }

    getConstraintById(id: number): AtomicConstraintValue {
        return this.constraints.getElementValueById(id) || [true, true, true];
    }

    /**
     * Returns array of atomic labels E.g., [1, 2, undefined, undefined]
     */
    get atomicLabelsArray(): (AtomicLabelValue | undefined)[] {
        const { labels } = this;
        const labelById = Object.fromEntries(
            labels.ids.map((id, index) => [id, labels.values[index]]),
        );
        return this._elements.ids.map((id) => labelById[id]);
    }

    /**
     * Returns array of elements with labels E.g., ["Fe1", "Fe2", "O", "O"]
     */
    override get elementsWithLabelsArray(): string[] {
        return this.atomicLabelsArray.map(
            (label, index) => `${this.getElementByIndex(index)}${label ?? ""}`,
        );
    }

    /**
     * Helper function returning a nested array with [element, label, coordinate, constraint] as elements
     */
    get elementsCoordinatesConstraintsArray(): [
        AtomicElementValue,
        AtomicLabelValue | undefined,
        AtomicCoordinateValue,
        AtomicConstraintValue,
    ][] {
        const { atomicLabelsArray, constraints } = this;
        const constraintById = Object.fromEntries(
            constraints.ids.map((id, index) => [id, constraints.values[index]]),
        );
        return this._elements.values.map((element: AtomicElementValue, idx: number) => {
            const coordinate = this.getCoordinateValueByIndex(idx);
            const constraint = constraintById[this._elements.ids[idx]] || [true, true, true];
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
        const omitConstraints = this.constraints.areUnconstrained;
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

    override get arraysWithIds(): ArrayWithIds<unknown>[] {
        return [
            ...super.arraysWithIds,
            ...this.atomicProperties.properties.map(({ values }) => values),
        ];
    }
}
