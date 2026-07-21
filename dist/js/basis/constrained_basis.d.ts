import { AtomicConstraintsSchema } from "@mat3ra/esse/dist/js/types";
import { AtomicConstraints, AtomicConstraintValue } from "../constraints/constraints";
import { Basis, BasisConfig, ElementsAndCoordinatesConfig } from "./basis";
import { AtomicCoordinateValue } from "./coordinates";
import { AtomicElementValue } from "./elements";
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
export declare class ConstrainedBasis extends Basis {
    private _constraints;
    constructor(config: ConstrainedBasisConfig);
    static fromElementsCoordinatesAndConstraints(config: ElementsCoordinatesAndConstraintsConfig): ConstrainedBasis;
    get constraints(): AtomicConstraintsSchema;
    set constraints(constraints: AtomicConstraintsSchema);
    get AtomicConstraints(): AtomicConstraints;
    toJSON(): ConstrainedBasisConfig;
    getConstraintByIndex(idx: number): AtomicConstraintValue;
    getConstraintById(id: number): AtomicConstraintValue;
    /**
     * Helper function returning a nested array with [element, coordinates, constraints] as elements
     */
    get elementsCoordinatesConstraintsArray(): [
        AtomicElementValue,
        AtomicLabelValue,
        AtomicCoordinateValue,
        AtomicConstraintValue
    ][];
    /**
     * Returns an array with atomic positions (with constraints) per atom stored as strings.
     * E.g., ``` ['Si  0 0 0  0 1 0', 'Li  0.5 0.5 0.5  1 0 1']```
     */
    getAtomicPositionsWithConstraintsAsStrings(coordinatePrintFormat?: string, precision?: number): string[];
    removeAllAtoms(): void;
}
