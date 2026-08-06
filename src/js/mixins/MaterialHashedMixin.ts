import type { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import {
    type HashedSchemaMixin,
    hashedSchemaMixin,
} from "@mat3ra/code/dist/js/generated/HashedSchemaMixin";
import type { MaterialSchema } from "@mat3ra/esse/dist/js/types";

type MaterialHashedMixinHost = {
    isNonPeriodic: boolean;
    calculateHash: (salt?: string, isScaled?: boolean, bypassNonPeriodicCheck?: boolean) => string;
};

export type MaterialHashedMixin = HashedSchemaMixin & {
    updateHash: () => void;
};

type MaterialHashedMixinProperties = MaterialHashedMixin & {
    basis: MaterialSchema["basis"];
    lattice: MaterialSchema["lattice"];
};

/**
 * Adds hash accessors plus basis/lattice setters that keep `hash` in sync.
 * Composes {@link hashedSchemaMixin}.
 */
export function materialHashedMixin<T extends InMemoryEntity>(
    item: InMemoryEntity,
): asserts item is T & MaterialHashedMixin {
    hashedSchemaMixin(item);

    // @ts-expect-error Mixin descriptor object: accessors use entity `this`.
    const properties: InMemoryEntity<MaterialSchema> &
        MaterialHashedMixinHost &
        MaterialHashedMixinProperties = {
        get basis() {
            return this.requiredProp("basis");
        },
        set basis(value: MaterialSchema["basis"]) {
            this.setProp("basis", value);
            this.updateHash();
        },
        get lattice() {
            return this.requiredProp("lattice");
        },
        set lattice(value: MaterialSchema["lattice"]) {
            this.setProp("lattice", value);
            this.updateHash();
        },
        updateHash() {
            this.hash = this.calculateHash("", false, this.isNonPeriodic);
        },
    };

    Object.defineProperties(item, Object.getOwnPropertyDescriptors(properties));
}
