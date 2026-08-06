import type { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import { type HashedSchemaMixin } from "@mat3ra/code/dist/js/generated/HashedSchemaMixin";
export type MaterialHashedMixin = HashedSchemaMixin & {
    updateHash: () => void;
};
/**
 * Adds hash accessors plus basis/lattice setters that keep `hash` in sync.
 * Composes {@link hashedSchemaMixin}.
 */
export declare function materialHashedMixin<T extends InMemoryEntity>(item: InMemoryEntity): asserts item is T & MaterialHashedMixin;
