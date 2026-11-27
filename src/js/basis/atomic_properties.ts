import { ArrayWithIds } from "@mat3ra/code";
import { AtomicPropertiesSchema, ProtoPropertyEnum } from "@mat3ra/esse/dist/js/types";

import { AtomicConstraints } from "../constraints/constraints";
import { Labels } from "./labels";

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

    /**
     * Returns the stored property, so that changes made to it are kept.
     */
    getByName<Name extends keyof AtomicPropertyByName>(name: Name): AtomicPropertyByName[Name] {
        return this.properties.find((item) => item.name === name)
            ?.values as AtomicPropertyByName[Name];
    }

    setByName<Name extends keyof AtomicPropertyByName>(
        name: Name,
        values: AtomicPropertyByName[Name],
    ) {
        this.properties = this.properties.map((item) =>
            item.name === name ? { name, values } : item,
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
