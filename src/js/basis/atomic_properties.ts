import { ArrayWithIds } from "@mat3ra/code";
import { AtomicPropertiesSchema, ProtoPropertyEnum } from "@mat3ra/esse/dist/js/types";

import { AtomicConstraints } from "../constraints/constraints";
import { Labels } from "./labels";

const ATOMIC_PROPERTY_CLASS_BY_NAME = {
    [ProtoPropertyEnum.atomic_constraints]: AtomicConstraints,
    [ProtoPropertyEnum.atomic_labels]: Labels,
};

type AtomicPropertyValuesByName = {
    [Name in keyof typeof ATOMIC_PROPERTY_CLASS_BY_NAME]: InstanceType<
        (typeof ATOMIC_PROPERTY_CLASS_BY_NAME)[Name]
    >;
};

type AtomicProperty = {
    name: AtomicPropertiesSchema[number]["name"];
    values: ArrayWithIds<unknown>;
};

/**
 * Per-atom properties of a basis, each keyed by atom id and stored under its proto-property name.
 */
export class AtomicProperties {
    readonly properties: AtomicProperty[];

    readonly propertyMapByName: Record<string, AtomicProperty>;

    /**
     * @param properties - the ESSE list of `{ name, values }` entries.
     */
    constructor(properties: AtomicPropertiesSchema = []) {
        this.properties = (
            Object.entries(ATOMIC_PROPERTY_CLASS_BY_NAME) as [
                keyof AtomicPropertyValuesByName,
                typeof ArrayWithIds,
            ][]
        ).map(([name, AtomicPropertyClass]) => ({
            name,
            values: AtomicPropertyClass.fromObjects(
                properties.find((property) => property.name === name)?.values ?? [],
            ),
        }));
        this.propertyMapByName = Object.fromEntries(
            this.properties.map((item) => [item.name, item]),
        );
    }

    /**
     * Returns the stored property, so that changes made to it are kept.
     */
    getByName<Name extends keyof AtomicPropertyValuesByName>(
        name: Name,
    ): AtomicPropertyValuesByName[Name] {
        return this.propertyMapByName[name].values as AtomicPropertyValuesByName[Name];
    }

    setByName<Name extends keyof AtomicPropertyValuesByName>(
        name: Name,
        values: AtomicPropertyValuesByName[Name],
    ) {
        this.propertyMapByName[name].values = values;
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
