import { type HashedSchemaMixin } from "@mat3ra/code/dist/js/generated/HashedSchemaMixin";
import type { BasisConstrainedSchema, MaterialConstrainedHashedSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";
import type { PartialBy } from "./Material";
import type Material from "./Material";
import MaterialConstrained from "./MaterialConstrained";
type Schema = MaterialConstrainedHashedSchema;
export type MaterialConstrainedHashedConfig<S extends Schema = Schema> = PartialBy<S, "name" | "metadata">;
export declare const defaultMaterialConstrainedHashedConfig: Schema;
interface MaterialConstrainedHashed extends HashedSchemaMixin {
}
declare class MaterialConstrainedHashed<S extends Schema = Schema> extends MaterialConstrained<S> {
    static createDefault: () => MaterialConstrainedHashed;
    static get defaultConfig(): MaterialConstrainedHashedConfig;
    static fromMaterial(material: Material | MaterialConstrained): MaterialConstrainedHashed;
    constructor(config: NoInfer<MaterialConstrainedHashedConfig<S>>);
    get basis(): BasisConstrainedSchema;
    set basis(value: BasisConstrainedSchema);
    protected setConstrainedBasis(basis: BasisConstrainedSchema): void;
    get lattice(): MaterialSchema["lattice"];
    set lattice(value: MaterialSchema["lattice"]);
    updateHash(): void;
}
export default MaterialConstrainedHashed;
