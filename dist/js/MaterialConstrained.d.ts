import type { AtomicConstraintsSchema, BasisSchema, MaterialConstrainedSchema } from "@mat3ra/esse/dist/js/types";
import type { BasisConfig } from "./basis/basis";
import { ConstrainedBasis } from "./basis/constrained_basis";
import Material, { type PartialBy } from "./Material";
type Schema = MaterialConstrainedSchema;
export type MaterialConstrainedConfig<S extends Schema = Schema> = PartialBy<S, "name" | "metadata">;
export declare const defaultMaterialConstrainedConfig: Schema;
declare class MaterialConstrained<S extends Schema = Schema> extends Material<S> implements Schema {
    static createDefault: () => MaterialConstrained;
    static get defaultConfig(): MaterialConstrainedConfig;
    static fromMaterial(material: Material | MaterialConstrained): MaterialConstrained;
    get basis(): S["basis"];
    set basis(basis: S["basis"]);
    protected setConstrainedBasis(basis: MaterialConstrainedSchema["basis"]): void;
    setBasis(basis: BasisConfig): void;
    setBasis(basis: string, format: "xyz", unitz?: BasisSchema["units"]): void;
    private setBasisConstraints;
    setBasisConstraintsFromArrayOfObjects(constraints: AtomicConstraintsSchema): void;
    getBasis(): ConstrainedBasis;
}
export default MaterialConstrained;
