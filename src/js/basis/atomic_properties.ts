import { ArrayWithIds } from "@mat3ra/code";
import type { AtomicPropertiesSchema } from "@mat3ra/esse/dist/js/types";

import { AtomicConstraints } from "../constraints/constraints";
import { Labels } from "./labels";

export enum ProtoPropertyEnum {
    atomic_constraints = "atomic_constraints",
    atomic_labels = "atomic_labels",
    boundary_conditions = "boundary_conditions",
}

const ATOMIC_PROPERTY_CLASS_BY_NAME = {
    [ProtoPropertyEnum.atomic_constraints]: AtomicConstraints,
    [ProtoPropertyEnum.atomic_labels]: Labels,
};

type AtomicPropertyByName = {
    [Name in keyof typeof ATOMIC_PROPERTY_CLASS_BY_NAME]: InstanceType<
        (typeof ATOMIC_PROPERTY_CLASS_BY_NAME)[Name]
    >;
};

/**
 * Per-atom properties of a basis, each keyed by atom id and stored under its proto-property name.
 */
export class AtomicProperties {
    properties: { name: AtomicPropertiesSchema[number]["name"]; values: ArrayWithIds<unknown> }[];

    /**
     * @param properties - the ESSE list of `{ name, values }` entries.
     */
    constructor(properties: AtomicPropertiesSchema = []) {
        this.properties = properties.map(({ name, values }) => ({
            name,
            values: (ATOMIC_PROPERTY_CLASS_BY_NAME[name] as typeof ArrayWithIds).fromObjects(
                values,
            ),
        }));
    }

    get propertyByName(): Record<string, ArrayWithIds<unknown>> {
        return Object.fromEntries(this.properties.map(({ name, values }) => [name, values]));
    }

    /**
     * Returns the stored property, storing an empty one first if absent, so that changes made to it are kept.
     */
    getByName<Name extends keyof AtomicPropertyByName>(name: Name): AtomicPropertyByName[Name] {
        if (!this.propertyByName[name]) {
            this.properties.push({ name, values: new ATOMIC_PROPERTY_CLASS_BY_NAME[name]() });
        }
        return this.propertyByName[name] as AtomicPropertyByName[Name];
    }

    setByName<Name extends keyof AtomicPropertyByName>(
        name: Name,
        property: AtomicPropertyByName[Name],
    ) {
        const index = this.properties.findIndex((item) => item.name === name);
        this.properties.splice(index < 0 ? this.properties.length : index, 1, {
            name,
            values: property,
        });
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
