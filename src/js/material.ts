import { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import {
    type Defaultable,
    defaultableEntityMixin,
} from "@mat3ra/code/dist/js/entity/mixins/DefaultableMixin";
import {
    type HasMetadata,
    hasMetadataMixin,
} from "@mat3ra/code/dist/js/entity/mixins/HasMetadataMixin";
import {
    type NamedEntity,
    namedEntityMixin,
} from "@mat3ra/code/dist/js/entity/mixins/NamedEntityMixin";
import type {
    AtomicConstraintsSchema,
    BasisSchema,
    ConsistencyCheck,
    DerivedPropertiesSchema,
    FileSourceSchema,
    InChIRepresentationSchema,
    LatticeSchema,
    MaterialSchema,
} from "@mat3ra/esse/dist/js/types";
import CryptoJS from "crypto-js";

import type { BasisConfig } from "./basis/basis";
import { type ConstrainedBasisConfig, ConstrainedBasis } from "./basis/constrained_basis";
import {
    isConventionalCellSameAsPrimitiveForLatticeType,
    PRIMITIVE_TO_CONVENTIONAL_CELL_LATTICE_TYPES,
    PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS,
} from "./cell/conventional_cell";
import { type MaterialSchemaMixin, materialSchemaMixin } from "./generated/MaterialSchemaMixin";
import { Lattice } from "./lattice/lattice";
import parsers from "./parsers/parsers";
import supercellTools from "./tools/supercell";

function parseBasis(
    textOrObject: string | BasisConfig,
    format?: "xyz",
    unitz?: BasisSchema["units"],
): ConstrainedBasisConfig {
    if (typeof textOrObject === "string") {
        if (format !== "xyz") {
            throw new Error("Invalid format");
        }
        return parsers.xyz.toBasisConfig(textOrObject, unitz);
    }
    return { constraints: [], ...textOrObject };
}

export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type MaterialConfig = PartialBy<MaterialSchema, "name" | "metadata">;

export const defaultMaterialConfig: MaterialConfig = {
    name: "Silicon FCC",
    basis: {
        elements: [
            {
                id: 0,
                value: "Si",
            },
            {
                id: 1,
                value: "Si",
            },
        ],
        coordinates: [
            {
                id: 0,
                value: [0.0, 0.0, 0.0],
            },
            {
                id: 1,
                value: [0.25, 0.25, 0.25],
            },
        ],
        units: "crystal",
    },
    lattice: {
        // Primitive cell for Diamond FCC Silicon at ambient conditions
        type: "FCC",
        a: 3.867,
        b: 3.867,
        c: 3.867,
        alpha: 60,
        beta: 60,
        gamma: 60,
        units: {
            length: "angstrom",
            angle: "degree",
        },
    },
    metadata: {},
};

interface BaseMaterial
    extends MaterialSchemaMixin,
        NamedEntity,
        Defaultable,
        Required<HasMetadata<MaterialSchema["metadata"]>> {}

class BaseMaterial extends InMemoryEntity<MaterialSchema> {}

materialSchemaMixin(BaseMaterial.prototype);
namedEntityMixin(BaseMaterial.prototype);
defaultableEntityMixin(BaseMaterial);
hasMetadataMixin(BaseMaterial.prototype);

class Material extends BaseMaterial implements MaterialSchema {
    declare static createDefault: () => Material;

    static get defaultConfig(): MaterialConfig {
        return defaultMaterialConfig;
    }

    static constructMaterialFileSource(
        fileName: string,
        fileContent: string,
        fileExtension: string,
    ): FileSourceSchema {
        return {
            extension: fileExtension,
            filename: fileName,
            text: fileContent,
            hash: CryptoJS.MD5(fileContent).toString(),
        };
    }

    private constraints: AtomicConstraintsSchema = [];

    constructor(config: MaterialConfig, constraints: AtomicConstraintsSchema = []) {
        super({
            ...config,
            formula: config.formula ?? "",
            name: config.name ?? config.formula ?? "",
            metadata: config.metadata ?? {},
        });

        this.formula = config.formula || this.getBasis().formula;
        this.name = this.name || this.formula;
        this.constraints = constraints;
    }

    updateFormula() {
        const basis = this.getBasis();
        this.formula = basis.formula;
        this.unitCellFormula = basis.unitCellFormula;
    }

    /**
     * @summary Returns the specific derived property (as specified by name) for a material.
     */
    getDerivedPropertyByName(name: string) {
        return this.getDerivedProperties().find((x) => x.name === name);
    }

    /**
     * @summary Returns the derived properties array for a material.
     */
    getDerivedProperties(): DerivedPropertiesSchema {
        return this.derivedProperties ?? [];
    }

    unsetFileProps() {
        this.unsetProp("src");
        this.unsetProp("icsdId");
        this.unsetProp("external");
    }

    setBasis(basis: BasisConfig): void;

    setBasis(basis: string, format: "xyz", unitz?: BasisSchema["units"]): void;

    setBasis(textOrObject: string | BasisConfig, format?: "xyz", unitz?: BasisSchema["units"]) {
        const { constraints, ...basis } = parseBasis(textOrObject, format, unitz);

        this.basis = basis;
        this.constraints = constraints;
        this.unsetFileProps();
        this.updateFormula();
    }

    getBasis(constraints?: AtomicConstraintsSchema) {
        const basisData = this.basis;

        return new ConstrainedBasis({
            ...basisData,
            cell: this.getLattice().vectors,
            constraints: constraints ?? this.constraints,
        });
    }

    setLattice(lattice: LatticeSchema) {
        const basis = this.getBasis();
        const originalIsInCrystalUnits = basis.isInCrystalUnits;

        basis.toCartesian();
        basis.cell = new Lattice(lattice).vectors;

        if (originalIsInCrystalUnits) {
            basis.toCrystal();
        }

        this.basis = basis.toJSON();
        this.lattice = lattice;

        this.unsetFileProps();
    }

    getLattice() {
        return new Lattice(this.lattice);
    }

    /**
     * High-level access to unique elements from material instead of basis.
     */
    get uniqueElements() {
        return this.getBasis().uniqueElements;
    }

    /**
     * Returns the inchi string from the derivedProperties for a non-periodic material, or throws an error if the
     *  inchi cannot be found.
     *  @returns {String}
     */
    getInchiStringForHash(): string {
        const inchi = this.getDerivedPropertyByName("inchi");
        if (inchi) {
            return (inchi as InChIRepresentationSchema).value;
        }
        throw new Error("Hash cannot be created. Missing InChI string in derivedProperties");
    }

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
    calculateHash(salt = "", isScaled = false, bypassNonPeriodicCheck = false): string {
        let message;
        if (!this.isNonPeriodic || bypassNonPeriodicCheck) {
            message =
                this.getBasis().hashString +
                "#" +
                this.getLattice().getHashString(isScaled) +
                "#" +
                salt;
        } else {
            message = this.getInchiStringForHash();
        }
        return CryptoJS.MD5(message).toString();
    }

    /**
     * Converts basis to crystal/fractional coordinates.
     */
    toCrystal(constraints: AtomicConstraintsSchema = []) {
        this.basis = this.getBasis(constraints).toCrystal().toJSON();
    }

    /**
     * Converts current material's basis coordinates to cartesian.
     * No changes if coordinates already cartesian.
     */
    toCartesian(constraints: AtomicConstraintsSchema = []) {
        this.basis = this.getBasis(constraints).toCartesian().toJSON();
    }

    /**
     * Returns material's basis in XYZ format.
     */
    getBasisAsXyz(fractional = false): string {
        return parsers.xyz.fromMaterial(this.toJSON(), fractional);
    }

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
    getAsQEFormat(): string {
        return parsers.espresso.toEspressoFormat(this.toJSON());
    }

    /**
     * Returns material in POSCAR format. Pass `true` to ignore original poscar source and re-serialize.
     */
    getAsPOSCAR(ignoreOriginal = false, omitConstraints = false): string {
        // By default return original source if exists
        if (this.src?.extension === "poscar" && !ignoreOriginal) {
            return this.src.text;
        }
        return parsers.poscar.toPoscar(this.toJSON(), omitConstraints);
    }

    /**
     * Returns a copy of the material with conventional cell constructed instead of primitive.
     */
    getACopyWithConventionalCell(): this {
        const material = this.clone();

        const lattice = this.getLattice();

        // if conventional and primitive cells are the same => return a copy.
        if (isConventionalCellSameAsPrimitiveForLatticeType(lattice.type)) {
            return material;
        }

        const conventionalSupercellMatrix =
            PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS[lattice.type];
        const conventionalLatticeType = PRIMITIVE_TO_CONVENTIONAL_CELL_LATTICE_TYPES[lattice.type];
        const config = supercellTools.generateConfig(this, conventionalSupercellMatrix);

        config.lattice.type = conventionalLatticeType;
        config.name = `${this.name} - conventional cell`;

        // @ts-expect-error
        return new this.constructor(config) as this;
    }

    /**
     * @summary a series of checks for the material and returns an array of results in ConsistencyChecks format.
     * @returns Array of checks results
     */
    getConsistencyChecks(): ConsistencyCheck[] {
        const basisChecks = this.getBasisConsistencyChecks();

        // any other Material checks can be added here

        return basisChecks;
    }

    /**
     * @summary a series of checks for the material's basis and returns an array of results in ConsistencyChecks format.
     * @returns Array of checks results
     */
    getBasisConsistencyChecks(): ConsistencyCheck[] {
        const checks: ConsistencyCheck[] = [];
        const limit = 1000;
        const basis = this.getBasis();

        if (basis.elements.length < limit) {
            const overlappingAtomsGroups = basis.getOverlappingAtoms();
            overlappingAtomsGroups.forEach(({ id1, id2, element1, element2 }) => {
                checks.push(
                    {
                        key: `basis.coordinates.${id1}`,
                        name: "atomsOverlap",
                        severity: "warning",
                        message: `Atom ${element1} is too close to ${element2} at position ${
                            id2 + 1
                        }`,
                    },
                    {
                        key: `basis.coordinates.${id2}`,
                        name: "atomsOverlap",
                        severity: "warning",
                        message: `Atom ${element2} is too close to ${element1} at position ${
                            id1 + 1
                        }`,
                    },
                );
            });
        }

        return checks;
    }

    toJSON(): MaterialSchema {
        const lattice = this.getLattice();
        const basis = this.getBasis();

        return {
            ...super.toJSON(),
            lattice: lattice.toJSON(),
            basis: basis.toJSON(),
            isNonPeriodic: this.isNonPeriodic,
        } as MaterialSchema;
    }
}

export { Material };
