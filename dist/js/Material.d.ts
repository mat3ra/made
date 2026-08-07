import { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import { type Defaultable } from "@mat3ra/code/dist/js/entity/mixins/DefaultableMixin";
import { type HasMetadata } from "@mat3ra/code/dist/js/entity/mixins/HasMetadataMixin";
import { type NamedEntity } from "@mat3ra/code/dist/js/entity/mixins/NamedEntityMixin";
import type { JSONSchema } from "@mat3ra/esse/dist/js/esse/utils";
import type { AtomicConstraintsSchema, BasisSchema, ConsistencyCheck, DerivedPropertiesSchema, FileSourceSchema, LatticeSchema, MaterialConstrainedHashedSchema, MaterialConstrainedSchema, MaterialHashedSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";
import { type BasisConfig } from "./basis/basis";
import { type ConstrainedBasisConfig, ConstrainedBasis } from "./basis/constrained_basis";
import { type MaterialSchemaMixin } from "./generated/MaterialSchemaMixin";
import { Lattice } from "./lattice/lattice";
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
/**
 * Bundle of material JSON-schema variants used by {@link Material} projections.
 * Web-app passes extended schemas here so `toJSON*` return types stay precise.
 */
export type MaterialSchemaMap = {
    pure: MaterialSchema;
    constrained: MaterialConstrainedSchema;
    hashed: MaterialHashedSchema;
    constrainedHashed: MaterialConstrainedHashedSchema;
};
/** Default ESSE schema map (no web-app extensions). */
export type DefaultMaterialSchemas = MaterialSchemaMap;
/**
 * Constructor config: constraints/hash optional — normalized in the constructor
 * (`parseConstrainedBasis` + {@link Material.updateHash}).
 */
export type MaterialConfig<S extends MaterialConstrainedHashedSchema = MaterialConstrainedHashedSchema> = Omit<PartialBy<S, "name" | "metadata" | "hash" | "scaledHash">, "basis"> & {
    basis: MaterialSchema["basis"] | MaterialConstrainedSchema["basis"];
};
export declare const defaultMaterialConfig: MaterialConstrainedSchema;
interface BaseMaterial<S extends MaterialConstrainedHashedSchema = MaterialConstrainedHashedSchema> extends MaterialSchemaMixin, NamedEntity, Defaultable, Required<HasMetadata<S["metadata"]>> {
}
declare class BaseMaterial<S extends MaterialConstrainedHashedSchema = MaterialConstrainedHashedSchema> extends InMemoryEntity<S> {
}
/**
 * Unified material. Pass extended schemas via {@link MaterialSchemaMap} so each
 * `toJSON*` returns the web-app (or other host) schema type.
 *
 * @example
 * ```ts
 * type WebappSchemas = {
 *   pure: MaterialSchema;
 *   constrained: WebappMaterialConstrainedSchema;
 *   hashed: WebappMaterialHashedSchema;
 *   constrainedHashed: WebappMaterialConstrainedSchema;
 * };
 * class CoreMaterial extends Material<WebappSchemas> {}
 * ```
 */
declare class Material<Schemas extends MaterialSchemaMap = DefaultMaterialSchemas> extends BaseMaterial<Schemas["constrainedHashed"]> {
    static createDefault: () => Material<MaterialSchemaMap>;
    /**
     * Schema used by {@link InMemoryEntity.clean} / {@link toJSON}.
     * Defaults to constrained+hashed; subclasses / web-app Core* may override.
     */
    static get jsonSchema(): JSONSchema;
    /** Schema for {@link toJSONPure} — override in web-app if the base material schema is extended. */
    static get jsonSchemaPure(): JSONSchema;
    /** Schema for {@link toJSONConstrained}. */
    static get jsonSchemaConstrained(): JSONSchema;
    /** Schema for {@link toJSONHashed}. */
    static get jsonSchemaHashed(): JSONSchema;
    /** Schema for {@link toJSONConstrainedHashed}. */
    static get jsonSchemaConstrainedHashed(): JSONSchema;
    static get defaultConfig(): MaterialConstrainedSchema;
    static constructMaterialFileSource(fileName: string, fileContent: string, fileExtension: string): FileSourceSchema;
    /**
     * @param config - Partial entity input. `basis.constraints` / `hash` may be omitted;
     *   both are filled in here before the instance is usable.
     * `NoInfer` keeps `Schemas` from being inferred from the config object literal.
     */
    constructor(config: NoInfer<MaterialConfig>);
    get hash(): Schemas["constrainedHashed"]["hash"];
    set hash(value: Schemas["constrainedHashed"]["hash"]);
    get scaledHash(): Schemas["constrainedHashed"]["scaledHash"];
    set scaledHash(value: Schemas["constrainedHashed"]["scaledHash"]);
    /** Recompute and store {@link hash} from the current basis/lattice. */
    updateHash(): void;
    get basis(): Schemas["constrainedHashed"]["basis"];
    set basis(value: Schemas["constrainedHashed"]["basis"]);
    get lattice(): Schemas["constrainedHashed"]["lattice"];
    set lattice(value: Schemas["constrainedHashed"]["lattice"]);
    updateFormula(): void;
    /**
     * @summary Returns the specific derived property (as specified by name) for a material.
     */
    getDerivedPropertyByName(name: string): {
        name?: "volume";
        units?: "angstrom^3";
        value: number;
    } | {
        name?: "density";
        units?: "g/cm^3";
        value: number;
    } | {
        pointGroupSymbol?: string;
        spaceGroupSymbol?: string;
        tolerance?: {
            units?: "angstrom";
            value: number;
        };
        name?: "symmetry";
    } | {
        name?: "elemental_ratio";
        value: number;
        element?: string;
    } | {
        name?: "p-norm";
        degree?: number;
        value: number;
    } | {
        name?: "inchi";
        value: string;
    } | {
        name?: "inchi_key";
        value: string;
    } | undefined;
    /**
     * @summary Returns the derived properties array for a material.
     */
    getDerivedProperties(): DerivedPropertiesSchema;
    unsetFileProps(): void;
    setBasis(basis: BasisConfig | ConstrainedBasisConfig): void;
    setBasis(basis: string, format: "xyz", units?: BasisSchema["units"]): void;
    private setBasisConstraints;
    setBasisConstraintsFromArrayOfObjects(constraints: AtomicConstraintsSchema): void;
    getBasis(): ConstrainedBasis;
    setLattice(lattice: LatticeSchema): void;
    getLattice(): Lattice;
    /**
     * High-level access to unique elements from material instead of basis.
     */
    get uniqueElements(): ("H" | "He" | "Li" | "Be" | "B" | "C" | "N" | "O" | "F" | "Ne" | "Na" | "Mg" | "Al" | "Si" | "P" | "S" | "Cl" | "Ar" | "K" | "Ca" | "Sc" | "Ti" | "V" | "Cr" | "Mn" | "Fe" | "Co" | "Ni" | "Cu" | "Zn" | "Ga" | "Ge" | "As" | "Se" | "Br" | "Kr" | "Rb" | "Sr" | "Y" | "Zr" | "Nb" | "Mo" | "Tc" | "Ru" | "Rh" | "Pd" | "Ag" | "Cd" | "In" | "Sn" | "Sb" | "Te" | "I" | "Xe" | "Cs" | "Ba" | "La" | "Ce" | "Pr" | "Nd" | "Pm" | "Sm" | "Eu" | "Gd" | "Tb" | "Dy" | "Ho" | "Er" | "Tm" | "Yb" | "Lu" | "Hf" | "Ta" | "W" | "Re" | "Os" | "Ir" | "Pt" | "Au" | "Hg" | "Tl" | "Pb" | "Bi" | "Po" | "At" | "Rn" | "Fr" | "Ra" | "Ac" | "Th" | "Pa" | "U" | "Np" | "Pu" | "Am" | "Cm" | "Bk" | "Cf" | "Es" | "Fm" | "Md" | "No" | "Lr" | "Rf" | "Db" | "Sg" | "Bh" | "Hs" | "Mt" | "Ds" | "Rg" | "Cn" | "Nh" | "Fl" | "Mc" | "Lv" | "Ts" | "Og" | "X" | "Vac")[];
    /**
     * Returns the inchi string from the derivedProperties for a non-periodic material, or throws an error if the
     *  inchi cannot be found.
     *  @returns {String}
     */
    getInchiStringForHash(): string;
    /**
     * Calculates hash from basis and lattice. Algorithm expects the following:
     * - asserts lattice units to be angstrom
     * - asserts basis units to be crystal
     * - asserts basis coordinates and lattice measurements are rounded to hash precision
     * - forms strings for lattice and basis
     * - creates MD5 hash from basisStr + latticeStr + salt
     * @param salt Salt for hashing, empty string by default.
     * @param isScaled Whether to scale the lattice parameter 'a' to 1.
     */
    calculateHash(salt?: string, isScaled?: boolean, bypassNonPeriodicCheck?: boolean): string;
    /**
     * Converts basis to crystal/fractional coordinates.
     */
    toCrystal(): void;
    /**
     * Converts current material's basis coordinates to cartesian.
     * No changes if coordinates already cartesian.
     */
    toCartesian(): void;
    /**
     * Returns material's basis in XYZ format.
     */
    getBasisAsXyz(fractional?: boolean): string;
    /**
     * Returns material in Quantum Espresso output format:
     * ```
     *    CELL_PARAMETERS (angstroms)
     *    -0.543131284  -0.000000000   0.543131284
     *    -0.000000000   0.543131284   0.543131284
     *    -0.543131284   0.543131284   0.000000000
     *
     *    ATOMIC_POSITIONS (crystal)
     *    Si       0.000000000   0.000000000  -0.000000000
     *    Si       0.250000000   0.250000000   0.250000000
     * ```
     */
    getAsQEFormat(): string;
    /**
     * Returns material in POSCAR format. Pass `true` to ignore original poscar source and re-serialize.
     */
    getAsPOSCAR(ignoreOriginal?: boolean, omitConstraints?: boolean): string;
    /**
     * Returns a copy of the material with conventional cell constructed instead of primitive.
     */
    getACopyWithConventionalCell(): this;
    /**
     * @summary a series of checks for the material and returns an array of results in ConsistencyChecks format.
     * @returns Array of checks results
     */
    getConsistencyChecks(): ConsistencyCheck[];
    /**
     * @summary a series of checks for the material's basis and returns an array of results in ConsistencyChecks format.
     * @returns Array of checks results
     */
    getBasisConsistencyChecks(): ConsistencyCheck[];
    /**
     * Full material JSON: constrained basis + hash fields from live getters.
     * Variants below AJV-clean this payload against the matching ESSE schema.
     * Builds from `_json` (not `super.toJSON`) so we do not pre-clean against
     * {@link Material.jsonSchema} before projecting to a narrower schema.
     */
    private getFullJSON;
    /**
     * Clone {@link getFullJSON} and validate/clean against `jsonSchema` via AJV
     * (same path as {@link InMemoryEntity.validateData} / {@link InMemoryEntity.clean}).
     */
    private cleanFullJSONAgainstSchema;
    toJSONPure(): Schemas["pure"];
    toJSONConstrained(): Schemas["constrained"];
    toJSONHashed(): Schemas["hashed"];
    toJSONConstrainedHashed(): Schemas["constrainedHashed"];
    toJSON(): Schemas["constrainedHashed"];
}
export default Material;
