import { type HashedSchemaMixin } from "@mat3ra/code/dist/js/generated/HashedSchemaMixin";
import type { AtomicConstraintsSchema, MaterialHashedSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";
import { type PartialBy, Material } from "./material";
export type MaterialHashedConfig = PartialBy<MaterialHashedSchema, "name" | "metadata" | "hash">;
interface MaterialHashed extends HashedSchemaMixin {
}
declare class MaterialHashed extends Material implements MaterialHashedSchema {
    static createDefault: () => MaterialHashed;
    static get defaultConfig(): MaterialHashedConfig;
    constructor(config: MaterialHashedConfig, constraints?: AtomicConstraintsSchema);
    get basis(): MaterialSchema["basis"];
    set basis(value: MaterialSchema["basis"]);
    get lattice(): MaterialSchema["lattice"];
    set lattice(value: MaterialSchema["lattice"]);
    updateHash(): void;
    toJSON(): MaterialHashedSchema;
}
export { MaterialHashed };
