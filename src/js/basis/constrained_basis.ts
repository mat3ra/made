import {
    AtomicConstraintsSchema,
    AtomicLabelsSchema,
    BasisConstrainedSchema,
    StartingMagnetizationSchema,
} from "@mat3ra/esse/dist/js/types";
import s from "underscore.string";

import { Cell } from "../cell/cell";
import { AtomicConstraints, AtomicConstraintValue, Constraint } from "../constraints/constraints";
import { Basis, ElementsAndCoordinatesConfig } from "./basis";
import { AtomicCoordinateValue, Coordinate } from "./coordinates";
import { AtomicElementValue } from "./elements";
import { AtomicLabelValue, Labels } from "./labels";
import { AtomicStartingMagnetizationValue, StartingMagnetization } from "./starting_magnetization";

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
    startingMagnetization: AtomicStartingMagnetizationValue;
}

/**
 * @summary Extension of the Basis class holding per-atom constraints, labels and starting magnetization.
 * @extends Basis
 */
export class ConstrainedBasis extends Basis<ConstrainedBasisConfig> {
    private _constraints: AtomicConstraints;

    private _labels: Labels;

    private _startingMagnetization: StartingMagnetization;

    constructor(config: ConstrainedBasisConfig) {
        super(config);
        this._constraints = AtomicConstraints.fromObjects(config.constraints ?? []); // `constraints` is an Array with ids
        this._labels = Labels.fromObjects(config.labels ?? []);
        this._startingMagnetization = StartingMagnetization.fromObjects(
            config.startingMagnetization ?? [],
        );
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

    get labels(): AtomicLabelsSchema {
        return this._labels.toJSON() as AtomicLabelsSchema;
    }

    set labels(labels: ConstrainedBasisConfig["labels"]) {
        this._labels = Labels.fromObjects(labels || []);
    }

    get startingMagnetization(): StartingMagnetizationSchema {
        return this._startingMagnetization.toJSON() as StartingMagnetizationSchema;
    }

    set startingMagnetization(
        startingMagnetization: ConstrainedBasisConfig["startingMagnetization"],
    ) {
        this._startingMagnetization = StartingMagnetization.fromObjects(
            startingMagnetization || [],
        );
    }

    override toJSON(exclude: (keyof ConstrainedBasisConfig)[] = ["cell"]): ConstrainedBasisConfig {
        return {
            ...super.toJSON([...exclude, "labels", "startingMagnetization"]),
            constraints: this.constraints,
            ...(this.labels?.length ? { labels: this.labels } : {}),
            ...(this.startingMagnetization?.length
                ? { startingMagnetization: this.startingMagnetization }
                : {}),
        };
    }

    /** Returns array of atomic labels by atom id E.g., [1, 2, undefined, undefined] */
    get atomicLabelsArray(): (AtomicLabelValue | undefined)[] {
        const { ids, values } = this._labels;
        const labelById = new Map(ids.map((id, index) => [id, values[index]] as const));
        return this._elements.ids.map((id) => labelById.get(id));
    }

    /** Returns array of starting magnetization by atom id E.g., [0.5, -0.5, 0, 0] */
    get startingMagnetizationArray(): number[] {
        const { ids, values } = this._startingMagnetization;
        const valueById = new Map(ids.map((id, index) => [id, values[index]] as const));
        return this._elements.ids.map((id) => valueById.get(id) ?? 0);
    }

    /** Returns array of elements with labels E.g., ["Fe1", "Fe2", "O", "O"] */
    get elementsWithLabelsArray(): string[] {
        return this.atomicLabelsArray.map(
            (label, index) => `${this.getElementByIndex(index)}${label ?? ""}`,
        );
    }

    /**
     * Returns the species: one per element and starting magnetization, in order of first appearance,
     * named "Fe", "Fe1", "Fe2" as Quantum ESPRESSO species names (at most 3 characters).
     */
    get uniqueAtomicSpecies(): AtomicSpecies[] {
        const species: AtomicSpecies[] = [];
        this.startingMagnetizationArray.forEach((startingMagnetization, index) => {
            const element = this.getElementByIndex(index);
            const speciesOfElement = species.filter((item) => item.element === element);
            const valuesOfElement = speciesOfElement.map((item) => item.startingMagnetization);
            if (valuesOfElement.includes(startingMagnetization)) return;
            const name = speciesOfElement.length ? `${element}${speciesOfElement.length}` : element;
            if (name.length > 3) {
                throw new Error(
                    `${element} has more than ${speciesOfElement.length} distinct starting magnetization values; species names are limited to 3 characters`,
                );
            }
            species.push({ name, element, startingMagnetization });
        });
        return species;
    }

    /** Returns array of species names by atom E.g., ["Fe", "Fe1", "O", "O"] */
    get atomicSpeciesArray(): AtomicSpecies["name"][] {
        const species = this.uniqueAtomicSpecies;
        return this.startingMagnetizationArray.map((startingMagnetization, index) => {
            const element = this.getElementByIndex(index);
            const speciesIndex = species.findIndex(
                (item) =>
                    item.element === element &&
                    item.startingMagnetization === startingMagnetization,
            );
            return species[speciesIndex].name;
        });
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
        return this._constraints.getElementValueByIndex(idx) || [true, true, true];
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
        const { atomicSpeciesArray } = this;
        return this._elements.values.map((element: AtomicElementValue, idx: number) => {
            const coordinate = this.getCoordinateValueByIndex(idx);
            const constraint = this.getConstraintByIndex(idx);
            return [element, atomicSpeciesArray[idx], coordinate, constraint];
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

    copyLabelsAndStartingMagnetizationByIndex(basis: ConstrainedBasis) {
        const ownIdByOtherId = new Map(
            basis._elements.ids.map((id, index) => [id, this._elements.ids[index]] as const),
        );
        const copyByIndex = <T extends { id: number }>(entries: T[]) =>
            entries
                .filter(({ id }) => ownIdByOtherId.get(id) !== undefined)
                .map((entry) => ({ ...entry, id: ownIdByOtherId.get(entry.id) as number }));
        this.labels = copyByIndex(basis.labels);
        this.startingMagnetization = copyByIndex(basis.startingMagnetization);
    }

    removeAllAtoms() {
        super.removeAllAtoms();
        this.constraints = [];
        this.labels = [];
        this.startingMagnetization = [];
    }
}
