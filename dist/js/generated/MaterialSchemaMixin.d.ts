import type { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import type { MaterialPropertiesSchema } from "@mat3ra/esse/dist/js/types";
export type MaterialSchemaMixin = MaterialPropertiesSchema;
export type MaterialInMemoryEntity = InMemoryEntity & MaterialSchemaMixin;
export declare function materialSchemaMixin<T extends InMemoryEntity>(item: InMemoryEntity): asserts item is T & MaterialSchemaMixin;
