import {
    type HashedSchemaMixin,
    hashedSchemaMixin,
} from "@mat3ra/code/dist/js/generated/HashedSchemaMixin";
import type { MaterialHashedSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";

import Material, { type MaterialConfig, type PartialBy, defaultMaterialConfig } from "./Material";

type Schema = MaterialHashedSchema;

export type MaterialHashedConfig<S extends Schema = Schema> = PartialBy<
    S,
    "name" | "metadata" | "hash"
>;

// eslint-disable-next-line @typescript-eslint/no-empty-interface
interface MaterialHashed extends HashedSchemaMixin {}

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

    get basis(): MaterialSchema["basis"] {
        return super.basis;
    }

    set basis(value: MaterialSchema["basis"]) {
        super.basis = value;
        this.updateHash();
    }

    get lattice(): MaterialSchema["lattice"] {
        return super.lattice;
    }

    set lattice(value: MaterialSchema["lattice"]) {
        super.lattice = value;
        this.updateHash();
    }

    updateHash() {
        this.hash = this.calculateHash("", false, this.isNonPeriodic);
    }
}

hashedSchemaMixin(MaterialHashed.prototype);

export default MaterialHashed;
