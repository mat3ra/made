import type { MaterialConstrainedHashedSchema } from "@mat3ra/esse/dist/js/types";
import type { PartialBy } from "./Material";
import type Material from "./Material";
import MaterialConstrained from "./MaterialConstrained";
import { type MaterialHashedMixin } from "./mixins/MaterialHashedMixin";
type Schema = MaterialConstrainedHashedSchema;
export type MaterialConstrainedHashedConfig<S extends Schema = Schema> = PartialBy<S, "name" | "metadata">;
export declare const defaultMaterialConstrainedHashedConfig: Schema;
interface MaterialConstrainedHashed extends MaterialHashedMixin {
}
declare class MaterialConstrainedHashed<S extends Schema = Schema> extends MaterialConstrained<S> {
    static createDefault: () => MaterialConstrainedHashed;
    static get defaultConfig(): MaterialConstrainedHashedConfig;
    static fromMaterial(material: Material | MaterialConstrained): MaterialConstrainedHashed;
    constructor(config: NoInfer<MaterialConstrainedHashedConfig<S>>);
}
export default MaterialConstrainedHashed;
