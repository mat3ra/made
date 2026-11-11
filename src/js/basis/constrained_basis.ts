import {
    AtomicConstraintsSchema,
    AtomicLabelsSchema,
    AtomicMagneticMomentsSchema,
    BasisConstrainedSchema,
} from "@mat3ra/esse/dist/js/types";
import { uniq } from "lodash";
import s from "underscore.string";

import { Cell } from "../cell/cell";
import { AtomicConstraints, AtomicConstraintValue, Constraint } from "../constraints/constraints";
import { Basis, ElementsAndCoordinatesConfig } from "./basis";
import { AtomicCoordinateValue, Coordinate } from "./coordinates";
import { AtomicElementValue } from "./elements";

export interface ConstrainedBasisConfig extends BasisConstrainedSchema {
    cell?: Cell;
    isEmpty?: boolean;
}

export interface ElementsCoordinatesAndConstraintsConfig extends ElementsAndCoordinatesConfig {
    constraints: AtomicConstraintValue[];
}

export interface AtomicSpecies {
    name: string;
    element: AtomicElementValue;
    magneticMoment: number;
}

type PerAtomValues = { id: number; value: unknown }[];

/**
 * @summary Extension of the Basis class holding per-atom constraints, labels and magnetic moments.
 * @extends Basis
 */
export class ConstrainedBasis extends Basis<ConstrainedBasisConfig> {
    static readonly PER_ATOM_KEYS = ["constraints", "labels", "magneticMoments"] as const;

    private _constraints: AtomicConstraints;

    labels: AtomicLabelsSchema;

    magneticMoments: AtomicMagneticMomentsSchema;

    constructor(config: ConstrainedBasisConfig) {
        super(config);
        this._constraints = AtomicConstraints.fromObjects(config.constraints ?? []); // `constraints` is an Array with ids
        this.labels = config.labels ?? [];
        this.magneticMoments = config.magneticMoments ?? [];
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
            ...super.toJSON(exclude),
            ...Object.fromEntries(ConstrainedBasis.PER_ATOM_KEYS.map((key) => [key, this[key]])),
        };
    }

    /** Returns the value of each atom, in basis order, from per-atom entries keyed by atom id */
    valuesByAtom<T>(entries: { id: number; value: T }[]): (T | undefined)[] {
        const valueById = new Map(entries.map(({ id, value }) => [id, value]));
        return this._elements.ids.map((id) => valueById.get(id));
    }

    /** Returns array of atomic labels by atom id E.g., [1, 2, undefined, undefined] */
    get atomicLabelsArray() {
        return this.valuesByAtom(this.labels);
    }

    /** Returns array of magnetic moments by atom id E.g., [0.5, -0.5, 0, 0] */
    get magneticMomentsArray(): number[] {
        return this.valuesByAtom(this.magneticMoments).map((value) => value ?? 0);
    }

    /** Returns array of elements with labels E.g., ["Fe1", "Fe2", "O", "O"] */
    get elementsWithLabelsArray(): string[] {
        return this.atomicLabelsArray.map(
            (label, index) => `${this.getElementByIndex(index)}${label ?? ""}`,
        );
    }

    /**
     * Returns the species of each atom: one per element and magnetic moment, in order of first
     * appearance, named "Fe", "Fe1", "Fe2" as Quantum ESPRESSO species names (at most 3 characters).
     */
    private get speciesOfAtoms(): AtomicSpecies[] {
        const species: AtomicSpecies[] = [];
        return this.magneticMomentsArray.map((magneticMoment, index) => {
            const element = this.getElementByIndex(index);
            const speciesOfElement = species.filter((item) => item.element === element);
            const found = speciesOfElement.find((item) => item.magneticMoment === magneticMoment);
            if (found) return found;
            const count = speciesOfElement.length;
            const name = count ? `${element}${count}` : element;
            if (name.length > 3) {
                throw new Error(
                    `${element} has more than ${count} distinct magnetic moments; species names are limited to 3 characters`,
                );
            }
            species.push({ name, element, magneticMoment });
            return species[species.length - 1];
        });
    }

    /** Returns the distinct species in order of first appearance E.g., [Fe, Fe1, O] */
    get uniqueAtomicSpecies(): AtomicSpecies[] {
        return uniq(this.speciesOfAtoms);
    }

    /** Returns array of species names by atom E.g., ["Fe", "Fe1", "O", "O"] */
    get atomicSpeciesArray(): AtomicSpecies["name"][] {
        return this.speciesOfAtoms.map(({ name }) => name);
    }

    /**
     * Returns an array of strings with species names and their atomic positions.
     * E.g., ``` ['Fe 0,0,0', 'Fe1 0.5,0.5,0.5']```
     */
    get atomicPositions(): string[] {
        return this.atomicSpeciesArray.map(
            (species, index) => `${species} ${this.getCoordinateValueByIndex(index)}`,
        );
    }

    getConstraintByIndex(idx: number): AtomicConstraintValue {
        // Not getElementIdByIndex: it returns `ids[index] || undefined`, so atom id 0 would lose its constraint.
        return this.getConstraintById(this._elements.ids[idx]);
    }

    getConstraintById(id: number): AtomicConstraintValue {
        return this._constraints.getElementValueById(id) || [true, true, true];
    }

    /**
     * Helper function returning a nested array with [element, species name, coordinates, constraints] as elements
     */
    get elementsCoordinatesConstraintsArray(): [
        AtomicElementValue,
        AtomicSpecies["name"],
        AtomicCoordinateValue,
        AtomicConstraintValue,
    ][] {
        const atomicSpecies = this.atomicSpeciesArray;
        return this._elements.values.map((element: AtomicElementValue, idx: number) => {
            const coordinate = this.getCoordinateValueByIndex(idx);
            const constraint = this.getConstraintByIndex(idx);
            return [element, atomicSpecies[idx], coordinate, constraint];
        });
    }

    /**
     * Returns an array with atomic positions (with constraints) per atom stored as strings.
     * E.g., ``` ['Si  0 0 0  0 1 0', 'Li  0.5 0.5 0.5  1 0 1']```
     * @param atomNames - species names for code inputs (default); XYZ passes elements with labels.
     */
    getAtomicPositionsWithConstraintsAsStrings(
        coordinatePrintFormat?: string,
        precision?: number,
        atomNames = this.atomicSpeciesArray,
    ): string[] {
        const omitConstraints = this._constraints.areUnconstrained;
        return atomNames.map((atomName, index) => {
            const _coordinate = Coordinate.fromValueAndId(this.getCoordinateValueByIndex(index));
            const _constraint = Constraint.fromValueAndId(this.getConstraintByIndex(index));

            return [
                s.sprintf("%-3s", atomName),
                _coordinate.prettyPrint(coordinatePrintFormat, precision),
                omitConstraints ? "" : _constraint.prettyPrint(),
            ].join(" ");
        });
    }

    /** Removes the atoms with the given ids together with their per-atom values */
    removeAtomsByIds(ids: number[]) {
        const isKept = ({ id }: { id: number }) => !ids.includes(id);
        this.elements = this.elements.filter(isKept);
        this.coordinates = this.coordinates.filter(isKept);
        ConstrainedBasis.PER_ATOM_KEYS.forEach((key) => {
            this[key] = (this[key] as PerAtomValues).filter(isKept) as never;
        });
    }

    removeAllAtoms() {
        super.removeAllAtoms();
        ConstrainedBasis.PER_ATOM_KEYS.forEach((key) => {
            this[key] = [];
        });
    }
}
