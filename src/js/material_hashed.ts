import {
    type HashedSchemaMixin,
    hashedSchemaMixin,
} from "@mat3ra/code/dist/js/generated/HashedSchemaMixin";
import type {
    AtomicConstraintsSchema,
    MaterialHashedSchema,
    MaterialSchema,
} from "@mat3ra/esse/dist/js/types";

import { type PartialBy, defaultMaterialConfig, Material } from "./material";

export type MaterialHashedConfig = PartialBy<MaterialHashedSchema, "name" | "metadata" | "hash">;

// eslint-disable-next-line @typescript-eslint/no-empty-interface
interface MaterialHashed extends HashedSchemaMixin {}

class MaterialHashed extends Material implements MaterialHashedSchema {
    declare static createDefault: () => MaterialHashed;

    static get defaultConfig(): MaterialHashedConfig {
        return defaultMaterialConfig;
    }

    constructor(config: MaterialHashedConfig, constraints: AtomicConstraintsSchema = []) {
        super(config, constraints);
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

    toJSON(): MaterialHashedSchema {
        return {
            ...super.toJSON(),
            hash: this.hash,
        } as MaterialHashedSchema;
    }
}

hashedSchemaMixin(MaterialHashed.prototype);

export { MaterialHashed };
