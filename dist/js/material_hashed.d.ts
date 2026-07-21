import { type HashedSchemaMixin } from "@mat3ra/code/dist/js/generated/HashedSchemaMixin";
import type { AtomicConstraintsSchema, MaterialHashedSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";
import { type PartialBy, Material } from "./material";
type Schema = MaterialHashedSchema;
export type MaterialHashedConfig<S extends Schema = Schema> = PartialBy<S, "name" | "metadata" | "hash">;
interface MaterialHashed extends HashedSchemaMixin {
}
declare class MaterialHashed<S extends Schema = Schema> extends Material<S> implements Schema {
    static createDefault: () => MaterialHashed;
    static get defaultConfig(): MaterialHashedConfig;
    constructor(config: NoInfer<MaterialHashedConfig<S>>, constraints?: AtomicConstraintsSchema);
    get basis(): MaterialSchema["basis"];
    set basis(value: MaterialSchema["basis"]);
    get lattice(): MaterialSchema["lattice"];
    set lattice(value: MaterialSchema["lattice"]);
    updateHash(): void;
}
export { MaterialHashed };
