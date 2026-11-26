import type { AtomicPropertiesSchema } from "@mat3ra/esse/dist/js/types";

import { AtomicConstraints } from "../constraints/constraints";
import { Labels } from "./labels";

export enum ProtoPropertyEnum {
    atomic_constraints = "atomic_constraints",
    atomic_labels = "atomic_labels",
    boundary_conditions = "boundary_conditions",
}

interface AtomicPropertyByName {
    [ProtoPropertyEnum.atomic_constraints]: AtomicConstraints;
    [ProtoPropertyEnum.atomic_labels]: Labels;
}

/**
 * Per-atom properties of a basis, each keyed by atom id and stored under its proto-property name.
 */
export class AtomicProperties {
    properties: {
        name: AtomicPropertiesSchema[number]["name"];
        values: AtomicConstraints | Labels;
    }[];

    /**
     * @param properties - the ESSE list of `{ name, values }` entries.
     */
    constructor(properties: AtomicPropertiesSchema = []) {
        this.properties = [
            {
                name: ProtoPropertyEnum.atomic_constraints,
                values: AtomicConstraints.fromObjects(
                    properties.flatMap((property) =>
                        property.name === ProtoPropertyEnum.atomic_constraints
                            ? property.values
                            : [],
                    ),
                ),
            },
            {
                name: ProtoPropertyEnum.atomic_labels,
                values: Labels.fromObjects(
                    properties.flatMap((property) =>
                        property.name === ProtoPropertyEnum.atomic_labels ? property.values : [],
                    ),
                ),
            },
        ];
    }

    get propertyByName(): Record<string, AtomicConstraints | Labels> {
        return Object.fromEntries(this.properties.map(({ name, values }) => [name, values]));
    }

    /**
     * Returns the stored property, so that changes made to it are kept.
     */
    getByName<Name extends keyof AtomicPropertyByName>(name: Name): AtomicPropertyByName[Name] {
        return this.propertyByName[name] as AtomicPropertyByName[Name];
    }

    setByName<Name extends keyof AtomicPropertyByName>(
        name: Name,
        property: AtomicPropertyByName[Name],
    ) {
        this.properties = this.properties.map((item) =>
            item.name === name ? { name, values: property } : item,
        );
    }

    /**
     * Returns the ESSE list; properties with no values are left out.
     */
    toJSON(): AtomicPropertiesSchema {
        return this.properties
            .filter(({ values }) => values.values.length)
            .map(({ name, values }) => ({
                name,
                values: values.toJSON(),
            })) as AtomicPropertiesSchema;
    }
}
