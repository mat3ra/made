import type {
    AtomicConstraintsSchema,
    BasisSchema,
    MaterialConstrainedSchema,
} from "@mat3ra/esse/dist/js/types";

import type { BasisConfig } from "./basis/basis";
import { type ConstrainedBasisConfig, ConstrainedBasis } from "./basis/constrained_basis";
import { Constraint } from "./constraints/constraints";
import Material, { type PartialBy, defaultMaterialConfig } from "./Material";
import parsers from "./parsers/parsers";

type Schema = MaterialConstrainedSchema;

export type MaterialConstrainedConfig<S extends Schema = Schema> = PartialBy<
    S,
    "name" | "metadata"
>;

export const defaultMaterialConstrainedConfig: Schema = {
    ...defaultMaterialConfig,
    basis: {
        ...defaultMaterialConfig.basis,
        constraints: [],
    },
};

function parseConstrainedBasis(
    textOrObject: string | BasisConfig | ConstrainedBasisConfig,
    format?: "xyz",
    unitz?: BasisSchema["units"],
): ConstrainedBasisConfig {
    if (typeof textOrObject === "string") {
        if (format !== "xyz") {
            throw new Error("Invalid format");
        }
        return parsers.xyz.toBasisConfig(textOrObject, unitz);
    }
    if ("constraints" in textOrObject) {
        return textOrObject;
    }
    return { ...textOrObject, constraints: [] };
}

class MaterialConstrained<S extends Schema = Schema> extends Material<S> implements Schema {
    declare static createDefault: () => MaterialConstrained;

    static get defaultConfig(): MaterialConstrainedConfig {
        return defaultMaterialConstrainedConfig;
    }

    static fromMaterial(material: Material | MaterialConstrained): MaterialConstrained {
        const constraints = "constraints" in material.basis ? material.basis.constraints : [];

        return new MaterialConstrained({
            ...material.toJSON(),
            basis: {
                ...material.basis,
                constraints,
            },
        });
    }

    get basis(): S["basis"] {
        return this.requiredProp("basis");
    }

    set basis(basis: S["basis"]) {
        super.basis = basis;
    }

    protected setConstrainedBasis(basis: MaterialConstrainedSchema["basis"]) {
        super.basis = basis;
    }

    setBasis(basis: BasisConfig): void;

    setBasis(basis: string, format: "xyz", unitz?: BasisSchema["units"]): void;

    setBasis(
        textOrObject: string | BasisConfig | ConstrainedBasisConfig,
        format?: "xyz",
        unitz?: BasisSchema["units"],
    ) {
        this.setConstrainedBasis(parseConstrainedBasis(textOrObject, format, unitz));
        this.unsetFileProps();
        this.updateFormula();
    }

    private setBasisConstraints(constraints: Constraint[]) {
        this.basis = {
            ...this.basis,
            constraints: constraints.map((constraint) => ({
                id: constraint.id,
                value: constraint.value,
            })),
        };
        this.unsetFileProps();
    }

    setBasisConstraintsFromArrayOfObjects(constraints: AtomicConstraintsSchema) {
        this.setBasisConstraints(
            constraints.map((constraint) =>
                Constraint.fromValueAndId(constraint.value, constraint.id),
            ),
        );
    }

    getBasis(): ConstrainedBasis {
        return new ConstrainedBasis({
            ...this.basis,
            cell: this.getLattice().vectors,
        });
    }
}

export default MaterialConstrained;
