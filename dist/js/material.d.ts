import { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import { type Defaultable } from "@mat3ra/code/dist/js/entity/mixins/DefaultableMixin";
import { type HasMetadata } from "@mat3ra/code/dist/js/entity/mixins/HasMetadataMixin";
import { type NamedEntity } from "@mat3ra/code/dist/js/entity/mixins/NamedEntityMixin";
import type { AtomicConstraintsSchema, BasisSchema, ConsistencyCheck, DerivedPropertiesSchema, FileSourceSchema, LatticeSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";
import type { BasisConfig } from "./basis/basis";
import { ConstrainedBasis } from "./basis/constrained_basis";
import { type MaterialSchemaMixin } from "./generated/MaterialSchemaMixin";
import { Lattice } from "./lattice/lattice";
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
type Schema = MaterialSchema;
export type MaterialConfig<S extends Schema = Schema> = PartialBy<S, "name" | "metadata">;
export declare const defaultMaterialConfig: Schema;
interface BaseMaterial extends MaterialSchemaMixin, NamedEntity, Defaultable, Required<HasMetadata<Schema["metadata"]>> {
}
declare class BaseMaterial<S extends Schema = Schema> extends InMemoryEntity<S> {
}
declare class Material<S extends Schema = Schema> extends BaseMaterial<S> implements Schema {
    static createDefault: () => Material;
    static get defaultConfig(): MaterialConfig;
    static constructMaterialFileSource(fileName: string, fileContent: string, fileExtension: string): FileSourceSchema;
    private constraints;
    constructor(config: NoInfer<MaterialConfig<S>>, constraints?: AtomicConstraintsSchema);
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
    setBasis(basis: BasisConfig): void;
    setBasis(basis: string, format: "xyz", unitz?: BasisSchema["units"]): void;
    getBasis(constraints?: AtomicConstraintsSchema): ConstrainedBasis;
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
    toCrystal(constraints?: AtomicConstraintsSchema): void;
    /**
     * Converts current material's basis coordinates to cartesian.
     * No changes if coordinates already cartesian.
     */
    toCartesian(constraints?: AtomicConstraintsSchema): void;
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
    toJSON(): S;
}
export { Material };
