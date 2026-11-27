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
        this.properties = (
            Object.entries(ATOMIC_PROPERTY_CLASS_BY_NAME) as [
                keyof AtomicPropertyByName,
                typeof ArrayWithIds,
            ][]
        ).map(([name, AtomicPropertyClass]) => ({
            name,
            values: AtomicPropertyClass.fromObjects(
                properties.find((property) => property.name === name)?.values ?? [],
            ),
        }));
    }

    get propertyByName(): Record<string, ArrayWithIds<unknown>> {
        return Object.fromEntries(this.properties.map(({ name, values }) => [name, values]));
    }

    /**
     * Returns the stored property, so that changes made to it are kept.
     */
    getByName<Name extends keyof AtomicPropertyByName>(name: Name): AtomicPropertyByName[Name] {
        return this.propertyByName[name] as AtomicPropertyByName[Name];
    }

    /**
     * Keeps the items of the given atom ids; with resetIds each id becomes its index in ids.
     */
    filterByIds(ids: number[], resetIds = false) {
        this.properties.forEach(({ values }) => {
            values.filterByIds(ids);
            if (resetIds) {
                values.ids = values.ids.map((id) => ids.indexOf(id));
            }
        });
    }

    /**
     * Adds the items of another one under the same names, with their atom ids shifted by idOffset.
     */
    addItemsFromAnother(other: AtomicProperties, idOffset: number) {
        const { propertyByName } = this;
        other.properties.forEach(({ name, values }) =>
            values.values.forEach((value, index) =>
                propertyByName[name].addItem(value, values.ids[index] + idOffset),
            ),
        );
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
