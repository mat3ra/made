import type { MaterialHashedSchema } from "@mat3ra/esse/dist/js/types";
import Material, { type PartialBy } from "./Material";
import { type MaterialHashedMixin } from "./mixins/MaterialHashedMixin";
type Schema = MaterialHashedSchema;
export type MaterialHashedConfig<S extends Schema = Schema> = PartialBy<S, "name" | "metadata" | "hash">;
interface MaterialHashed extends MaterialHashedMixin {
}
declare class MaterialHashed<S extends Schema = Schema> extends Material<S> implements Schema {
    static createDefault: () => MaterialHashed;
    static get defaultConfig(): MaterialHashedConfig;
    static fromMaterial(material: Material | MaterialHashed): MaterialHashed;
    constructor(config: NoInfer<MaterialHashedConfig<S>>);
}
export default MaterialHashed;
