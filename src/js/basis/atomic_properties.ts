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
    private propertyByName: AtomicPropertyByName;

    /**
     * @param properties - the ESSE list of `{ name, values }` entries.
     */
    constructor(properties: AtomicPropertiesSchema = []) {
        this.propertyByName = {
            [ProtoPropertyEnum.atomic_constraints]: AtomicConstraints.fromObjects(
                properties.flatMap((property) =>
                    property.name === ProtoPropertyEnum.atomic_constraints ? property.values : [],
                ),
            ),
            [ProtoPropertyEnum.atomic_labels]: Labels.fromObjects(
                properties.flatMap((property) =>
                    property.name === ProtoPropertyEnum.atomic_labels ? property.values : [],
                ),
            ),
        };
    }

    /**
     * Returns the stored property, so that changes made to it are kept.
     */
    getByName<Name extends keyof AtomicPropertyByName>(name: Name): AtomicPropertyByName[Name] {
        return this.propertyByName[name];
    }

    setByName<Name extends keyof AtomicPropertyByName>(
        name: Name,
        property: AtomicPropertyByName[Name],
    ) {
        this.propertyByName[name] = property;
    }

    /**
     * Returns the ESSE list; properties with no values are left out.
     */
    toJSON(): AtomicPropertiesSchema {
        return Object.entries(this.propertyByName)
            .filter(([, property]) => property.values.length)
            .map(([name, property]) => ({
                name,
                values: property.toJSON(),
            })) as AtomicPropertiesSchema;
    }
}
