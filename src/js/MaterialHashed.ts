import type { MaterialHashedSchema } from "@mat3ra/esse/dist/js/types";

import Material, { type MaterialConfig, type PartialBy, defaultMaterialConfig } from "./Material";
import { type MaterialHashedMixin, materialHashedMixin } from "./mixins/MaterialHashedMixin";

type Schema = MaterialHashedSchema;

export type MaterialHashedConfig<S extends Schema = Schema> = PartialBy<
    S,
    "name" | "metadata" | "hash"
>;

// eslint-disable-next-line @typescript-eslint/no-empty-interface
interface MaterialHashed extends MaterialHashedMixin {}

class MaterialHashed<S extends Schema = Schema> extends Material<S> implements Schema {
    declare static createDefault: () => MaterialHashed;

    static get defaultConfig(): MaterialHashedConfig {
        return defaultMaterialConfig;
    }

    static fromMaterial(material: Material | MaterialHashed): MaterialHashed {
        return new MaterialHashed({
            ...material.toJSON(),
            hash: material.calculateHash("", false, material.isNonPeriodic),
        });
    }

    // NoInfer: keep default S (or an explicit type arg) instead of inferring S from the config literal.
    constructor(config: NoInfer<MaterialHashedConfig<S>>) {
        // MaterialConfig<S> still requires hash; use a placeholder until calculateHash can run.
        super({
            ...config,
            hash: config.hash ?? "",
        } as MaterialConfig<S>);
        this.hash = config.hash ?? this.calculateHash("", false, this.isNonPeriodic);
    }
}

materialHashedMixin(MaterialHashed.prototype);

export default MaterialHashed;
