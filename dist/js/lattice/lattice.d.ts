import { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import { BaseInMemoryEntitySchema, LatticeSchema, LatticeTypeEnum, LatticeTypeExtendedEnum, LatticeVectorsSchema, Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Cell } from "../cell/cell";
import { UnitCell } from "./unit_cell";
/**
 * Scaling factor used to calculate the new lattice size for non-periodic systems.
 * The scaling factor ensures that a non-periodic structure will have have a lattice greater than the structures size.
 */
export { defaultNonPeriodicMinimumLatticeSize, diatomicLatticePaddingFactor, molecularLatticePaddingFactor, } from "../constants/molecule";
export declare class LatticeVectors extends Cell implements LatticeVectorsSchema {
}
export type { LatticeVectorsSchema };
type LatticeEntitySchema = LatticeSchema & BaseInMemoryEntitySchema;
export declare class Lattice extends InMemoryEntity<LatticeEntitySchema> implements LatticeSchema {
    static defaultConfig: LatticeSchema;
    a: LatticeSchema["a"];
    b: LatticeSchema["b"];
    c: LatticeSchema["c"];
    alpha: LatticeSchema["alpha"];
    beta: LatticeSchema["beta"];
    gamma: LatticeSchema["gamma"];
    type: LatticeTypeEnum;
    units: LatticeSchema["units"];
    constructor(config?: LatticeSchema);
    static fromConfig(config: object): Lattice;
    static fromConfigPartial(config: LatticeSchema): Lattice;
    calculateVectors(): Matrix3X3Schema;
    static fromVectors(config: LatticeVectorsSchema): Lattice;
    static fromVectorsArray(vectors: Matrix3X3Schema, units?: LatticeSchema["units"], type?: LatticeTypeEnum): Lattice;
    get unitCell(): UnitCell;
    get vectors(): LatticeVectors;
    get vectorArrays(): Matrix3X3Schema;
    get vectorArraysRounded(): Matrix3X3Schema;
    get cellVolume(): number;
    get cellVolumeRounded(): number;
    /**
     * Get a short label for the type of the lattice, eg. "MCLC".
     */
    get typeLabel(): string;
    /**
     * Get a short label for the extended type of the lattice, eg. "MCLC-5".
     */
    get typeExtended(): LatticeTypeExtendedEnum;
    /**
     * Calculate the volume of the lattice cell.
     */
    get volume(): number;
    static getDefaultPrimitiveLatticeConfigByType(latticeConfig: LatticeSchema): LatticeSchema & {
        a: unknown;
        b: unknown;
        c: unknown;
        alpha: unknown;
        beta: unknown;
        gamma: unknown;
    };
    /**
     * Returns a string further used for the calculation of an unique hash.
     * @param isScaled - Whether to scale the vectors by the length of the first vector initially.
     */
    getHashString(isScaled?: boolean): string;
    /**
     * Get the list of editable keys (eg. 'a', 'alpha') for the current lattice.
     * @return {Object}
     * @example {a: true, b: false, c: false, alpha: true, beta: false, gamma: false}
     */
    get editables(): {};
    toJSON(exclude?: (keyof LatticeSchema)[]): LatticeSchema;
}
