import { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import {
    BaseInMemoryEntitySchema,
    Coordinate3DSchema,
    LatticeSchema,
    LatticeTypeEnum,
    LatticeTypeExtendedEnum,
    LatticeVectorsSchema,
    Matrix3X3Schema,
} from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import * as lodash from "lodash";

import { Cell } from "../cell/cell";
import { PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS } from "../cell/conventional_cell";
import { getPrimitiveLatticeVectorsFromConfig } from "../cell/primitive_cell";
import { LATTICE_TYPE_CONFIGS } from "./lattice_types";
import { UnitCell, UnitCellProps } from "./unit_cell";

const { HASH_TOLERANCE } = Utils.constants;
/**
 * Scaling factor used to calculate the new lattice size for non-periodic systems.
 * The scaling factor ensures that a non-periodic structure will have have a lattice greater than the structures size.
 */
export {
    defaultNonPeriodicMinimumLatticeSize,
    diatomicLatticePaddingFactor,
    molecularLatticePaddingFactor,
} from "../constants/molecule";

export class LatticeVectors extends Cell implements LatticeVectorsSchema {}

export type { LatticeVectorsSchema };

type LatticeEntitySchema = LatticeSchema & BaseInMemoryEntitySchema;

export class Lattice extends InMemoryEntity<LatticeEntitySchema> implements LatticeSchema {
    static defaultConfig: LatticeSchema = {
        a: 1,
        b: 1,
        c: 1,
        alpha: 90,
        beta: 90,
        gamma: 90,
        units: { length: "angstrom", angle: "degree" },
        type: "CUB",
    };

    a: LatticeSchema["a"];

    b: LatticeSchema["b"];

    c: LatticeSchema["c"];

    alpha: LatticeSchema["alpha"];

    beta: LatticeSchema["beta"];

    gamma: LatticeSchema["gamma"];

    type: LatticeTypeEnum = "TRI";

    units: LatticeSchema["units"];

    constructor(config: LatticeSchema = Lattice.defaultConfig) {
        super(config);
        const { a, b, c, alpha, beta, gamma, units, type } = config;
        this.a = a;
        this.b = b;
        this.c = c;
        this.alpha = alpha;
        this.beta = beta;
        this.gamma = gamma;
        this.units = units;
        this.type = type || "TRI";
    }

    static fromConfig(config: object): Lattice {
        const latticeConfig = config as LatticeSchema;
        return new Lattice(latticeConfig);
    }

    static fromConfigPartial(config: LatticeSchema): Lattice {
        const primitiveLatticeConfig = Lattice.getDefaultPrimitiveLatticeConfigByType(config);
        return new Lattice(primitiveLatticeConfig);
    }

    calculateVectors(): Matrix3X3Schema {
        const { a } = this;
        const { b } = this;
        const { c } = this;

        const alphaRad = Utils.math.unit(this.alpha, "deg").toNumber("rad");
        const betaRad = Utils.math.unit(this.beta, "deg").toNumber("rad");
        const gammaRad = Utils.math.unit(this.gamma, "deg").toNumber("rad");

        const cosAlpha = Utils.math.cos(alphaRad);
        const cosBeta = Utils.math.cos(betaRad);
        const cosGamma = Utils.math.cos(gammaRad);
        const sinAlpha = Utils.math.sin(alphaRad);
        const sinBeta = Utils.math.sin(betaRad);

        const gammaStar = Utils.math.acos((cosAlpha * cosBeta - cosGamma) / (sinAlpha * sinBeta));
        // @ts-ignore - mathjs v12 acos return type includes Complex, but inputs are always real
        const cosGammaStar = Utils.math.cos(gammaStar);
        // @ts-ignore
        const sinGammaStar = Utils.math.sin(gammaStar);

        const vectorA: Coordinate3DSchema = [a * sinBeta, 0.0, a * cosBeta];
        const vectorB: Coordinate3DSchema = [
            -b * sinAlpha * cosGammaStar,
            b * sinAlpha * sinGammaStar,
            b * cosAlpha,
        ];
        const vectorC: Coordinate3DSchema = [0.0, 0.0, c];

        return [vectorA, vectorB, vectorC];
    }

    static fromVectors(config: LatticeVectorsSchema): Lattice {
        return this.fromVectorsArray([config.a, config.b, config.c]);
    }

    static fromVectorsArray(
        vectors: Matrix3X3Schema,
        units: LatticeSchema["units"] = Lattice.defaultConfig.units,
        type: LatticeTypeEnum = "TRI",
    ): Lattice {
        const [aVec, bVec, cVec] = vectors;
        const a = Utils.math.vlen(aVec);
        const b = Utils.math.vlen(bVec);
        const c = Utils.math.vlen(cVec);
        const alpha = Utils.math.angle(bVec, cVec, "deg");
        const beta = Utils.math.angle(aVec, cVec, "deg");
        const gamma = Utils.math.angle(aVec, bVec, "deg");

        return new Lattice({
            a,
            b,
            c,
            alpha,
            beta,
            gamma,
            units,
            type,
        });
    }

    // TODO: remove
    get unitCell() {
        const units = this.units?.length || "angstrom";
        const vectors = [...lodash.flatten(this.vectorArrays), units] as UnitCellProps;
        return new UnitCell(vectors);
    }

    get vectors(): LatticeVectors {
        return LatticeVectors.fromVectorsArray(this.calculateVectors());
    }

    get vectorArrays(): Matrix3X3Schema {
        return this.vectors.vectorArrays;
    }

    /**
     * The conventional cell of this primitive lattice, as lattice parameters.
     *
     * The conventional vectors are the type's multiplier times the primitive ones (Setyawan
     * and Curtarolo, doi:10.1016/j.commatsci.2010.05.010); alpha is the angle between the
     * second and third, as the monoclinic standard cells use it.
     */
    getConventionalLatticeParameters(): Lattice {
        const multiplier = PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS[this.type];
        const conventionalVectors = Utils.math.multiply(
            multiplier,
            this.vectorArrays,
        ) as Matrix3X3Schema;
        return Lattice.fromVectorsArray(conventionalVectors, this.units, this.type);
    }

    /**
     * `vectorArrays` rotated into the standard orientation of the lattice type.
     *
     * Lattice parameters fix a cell's shape but not its orientation. `vectorArrays` puts the
     * third vector along z for every type, which leaves the symmetry axes of most centred
     * lattices tilted; the standard primitive cells (`PRIMITIVE_CELLS`) have the conventional
     * axes along x, y and z, where programs that look for symmetry only about the Cartesian
     * axes, such as Quantum ESPRESSO's pw.x, find the full point group.
     *
     * The rotation R solves vectors · R = standard and is used only when it is proper and
     * exact, so a lattice not shaped like its type keeps `vectorArrays`. A rotation changes
     * no lengths or angles, so fractional coordinates stay valid; Cartesian coordinates
     * follow `vectorArrays`, which is unchanged.
     */
    get vectorArraysInStandardOrientation(): Matrix3X3Schema {
        const vectors = this.vectorArrays;
        if (!(this.type in PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS)) return vectors;
        const standard = getPrimitiveLatticeVectorsFromConfig(
            this.getConventionalLatticeParameters(),
        );
        const rotation = Utils.math.multiply(Utils.math.inv(vectors), standard) as Matrix3X3Schema;
        const deviation = Utils.math.subtract(
            Utils.math.multiply(Utils.math.transpose(rotation), rotation),
            Utils.math.identity(3),
        );
        const isOrthogonal =
            (Utils.math.norm(deviation as Matrix3X3Schema, "fro") as number) <= 1e-6;
        const isProper = (Utils.math.det(rotation) as number) > 0;
        return isOrthogonal && isProper ? standard : vectors;
    }

    get vectorArraysRounded(): Matrix3X3Schema {
        return this.vectors.vectorArraysRounded;
    }

    get cellVolume(): number {
        return this.vectors.volume;
    }

    get cellVolumeRounded(): number {
        return this.vectors.volumeRounded;
    }

    /**
     * Get a short label for the type of the lattice, eg. "MCLC".
     */
    get typeLabel(): string {
        return lodash.get(
            LATTICE_TYPE_CONFIGS.find((c) => c.code === this.type),
            "label",
            "Unknown",
        );
    }

    /**
     * Get a short label for the extended type of the lattice, eg. "MCLC-5".
     */
    get typeExtended(): LatticeTypeExtendedEnum {
        const { a, b, c, alpha, beta, gamma, type } = this;
        const cosAlpha = Utils.math.cos((alpha / 180) * Utils.math.PI);

        switch (type) {
            case "BCT":
                return c < a ? "BCT-1" : "BCT-2";
            case "ORCF":
                if (1 / (a * a) >= 1 / (b * b) + 1 / (c * c)) {
                    return "ORCF-1";
                }
                return "ORCF-2";
            case "RHL":
                return cosAlpha > 0 ? "RHL-1" : "RHL-2";
            case "MCLC":
                if (gamma >= 90) {
                    // MCLC-1,2
                    return "MCLC-1";
                }
                if ((b / c) * cosAlpha + ((b * b) / (a * a)) * (1 - cosAlpha * cosAlpha) <= 1) {
                    // MCLC-3,4
                    return "MCLC-3";
                }
                return "MCLC-5";
            case "TRI":
                if (alpha > 90 && beta > 90 && gamma >= 90) {
                    // TRI-1a,2a
                    return "TRI_1a";
                }
                return "TRI_1b";
            default:
                return type;
        }
    }

    /**
     * Calculate the volume of the lattice cell.
     */
    get volume(): number {
        return Utils.math.abs(Utils.math.det(this.vectorArrays));
    }

    /*
     * Returns a "default" primitive lattice by type, with lattice parameters scaled by the length of "a",
     * @param latticeConfig {Object} LatticeBravais config (see constructor)
     */
    static getDefaultPrimitiveLatticeConfigByType(latticeConfig: LatticeSchema) {
        const f_ = Utils.math.roundArrayOrNumber;
        // construct new primitive cell using lattice parameters and skip rounding the vectors
        const vectors = getPrimitiveLatticeVectorsFromConfig(latticeConfig);
        // create new lattice from primitive cell
        const newLattice = Lattice.fromVectorsArray(vectors, undefined, latticeConfig.type);
        // preserve the new type and scale back the lattice parameters
        const k = latticeConfig.a / newLattice.a;

        return Object.assign(newLattice.toJSON(), {
            a: f_(newLattice.a * k),
            b: f_(newLattice.b * k),
            c: f_(newLattice.c * k),
            alpha: f_(newLattice.alpha),
            beta: f_(newLattice.beta),
            gamma: f_(newLattice.gamma),
        });
    }

    /**
     * Returns a string further used for the calculation of an unique hash.
     * @param isScaled - Whether to scale the vectors by the length of the first vector initially.
     */
    getHashString(isScaled = false): string {
        // lattice vectors must be measured in angstroms
        const scaleK = isScaled ? this.a : 1;
        const scaledLattice = {
            ...this,
            a: this.a / scaleK,
            b: this.b / scaleK,
            c: this.c / scaleK,
        };
        // form lattice string
        return `${[
            scaledLattice.a,
            scaledLattice.b,
            scaledLattice.c,
            scaledLattice.alpha,
            scaledLattice.beta,
            scaledLattice.gamma,
        ]
            .map((x) => Utils.math.roundCustom(x, HASH_TOLERANCE))
            .join(";")};`;
    }

    /**
     * Get the list of editable keys (eg. 'a', 'alpha') for the current lattice.
     * @return {Object}
     * @example {a: true, b: false, c: false, alpha: true, beta: false, gamma: false}
     */
    get editables() {
        const object = {};
        const editablesList = LATTICE_TYPE_CONFIGS.find(
            (entry: any) => entry.code === this.type,
        )?.editables;
        // ["a", "gamma"] => {a: true, gamma: true}
        if (editablesList) {
            editablesList.forEach((element: any) => {
                Object.assign(object, {
                    [element]: true,
                });
            });
        }

        return object;
    }

    toJSON(exclude: (keyof LatticeSchema)[] = []): LatticeSchema {
        return {
            ...super.toJSON(exclude),
            vectors: this.vectors.toJSON(),
        };
    }
}
