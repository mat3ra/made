import {
    type HashedSchemaMixin,
    hashedSchemaMixin,
} from "@mat3ra/code/dist/js/generated/HashedSchemaMixin";
import type {
    BasisConstrainedSchema,
    MaterialConstrainedHashedSchema,
    MaterialSchema,
} from "@mat3ra/esse/dist/js/types";

import type { PartialBy } from "./Material";
import type Material from "./Material";
import MaterialConstrained, { defaultMaterialConstrainedConfig } from "./MaterialConstrained";

type Schema = MaterialConstrainedHashedSchema;

export type MaterialConstrainedHashedConfig<S extends Schema = Schema> = PartialBy<
    S,
    "name" | "metadata"
>;

export const defaultMaterialConstrainedHashedConfig: Schema = {
    ...defaultMaterialConstrainedConfig,
    hash: "",
};

// eslint-disable-next-line @typescript-eslint/no-empty-interface
interface MaterialConstrainedHashed extends HashedSchemaMixin {}

class MaterialConstrainedHashed<S extends Schema = Schema> extends MaterialConstrained<S> {
    declare static createDefault: () => MaterialConstrainedHashed;

    static get defaultConfig(): MaterialConstrainedHashedConfig {
        return defaultMaterialConstrainedHashedConfig;
    }

    static fromMaterial(material: Material | MaterialConstrained): MaterialConstrainedHashed {
        const constraints = "constraints" in material.basis ? material.basis.constraints : [];

        return new MaterialConstrainedHashed({
            ...material.toJSON(),
            basis: {
                ...material.basis,
                constraints,
            },
            hash: material.calculateHash("", false, material.isNonPeriodic),
        });
    }

    constructor(config: NoInfer<MaterialConstrainedHashedConfig<S>>) {
        super(config);
        this.hash = config.hash || this.calculateHash("", false, this.isNonPeriodic);
    }

    get basis(): BasisConstrainedSchema {
        return super.basis;
    }

    set basis(value: BasisConstrainedSchema) {
        super.basis = value;
        this.updateHash();
    }

    protected setConstrainedBasis(basis: BasisConstrainedSchema) {
        super.setConstrainedBasis(basis);
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

hashedSchemaMixin(MaterialConstrainedHashed.prototype);

export default MaterialConstrainedHashed;
