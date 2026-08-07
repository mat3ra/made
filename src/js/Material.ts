import { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import { EntityError } from "@mat3ra/code/dist/js/entity/in_memory";
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
import { clone, deepClone } from "@mat3ra/code/dist/js/utils/clone";
import JSONSchemasInterface from "@mat3ra/esse/dist/js/esse/JSONSchemasInterface";
import type { JSONSchema } from "@mat3ra/esse/dist/js/esse/utils";
import type {
    AtomicConstraintsSchema,
    BasisSchema,
    ConsistencyCheck,
    DerivedPropertiesSchema,
    FileSourceSchema,
    InChIRepresentationSchema,
    LatticeSchema,
    MaterialEnhancedHashedSchema,
    MaterialEnhancedSchema,
    MaterialHashedSchema,
    MaterialSchema,
} from "@mat3ra/esse/dist/js/types";
import CryptoJS from "crypto-js";

import { type BasisConfig } from "./basis/basis";
import { type ConstrainedBasisConfig, ConstrainedBasis } from "./basis/constrained_basis";
import {
    isConventionalCellSameAsPrimitiveForLatticeType,
    PRIMITIVE_TO_CONVENTIONAL_CELL_LATTICE_TYPES,
    PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS,
} from "./cell/conventional_cell";
import { Constraint } from "./constraints/constraints";
import { type MaterialSchemaMixin, materialSchemaMixin } from "./generated/MaterialSchemaMixin";
import { Lattice } from "./lattice/lattice";
import parsers from "./parsers/parsers";
import supercellTools from "./tools/supercell";

/** ESSE `$id` values for material schema variants. */
const MATERIAL_SCHEMA_IDS = {
    pure: "material",
    enhanced: "material-enhanced",
    hashed: "material-hashed",
    enhancedHashed: "material-enhanced-hashed",
} as const;

function parseConstrainedBasis(
    textOrObject: string | BasisConfig | ConstrainedBasisConfig,
    format?: "xyz",
    units?: BasisSchema["units"],
): ConstrainedBasisConfig {
    if (typeof textOrObject === "string") {
        if (format !== "xyz") {
            throw new Error("Invalid format");
        }
        return parsers.xyz.toBasisConfig(textOrObject, units);
    }
    if ("constraints" in textOrObject) {
        return textOrObject;
    }
    return { ...textOrObject, constraints: [] };
}

export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/**
 * Bundle of material JSON-schema variants used by {@link Material} projections.
 * Web-app passes extended schemas here so `toJSON*` return types stay precise.
 */
export type MaterialSchemaMap = {
    pure: MaterialSchema;
    enhanced: MaterialEnhancedSchema;
    hashed: MaterialHashedSchema;
    enhancedHashed: MaterialEnhancedHashedSchema;
};

/** Default ESSE schema map (no web-app extensions). */
export type DefaultMaterialSchemas = MaterialSchemaMap;

/**
 * Constructor config: constraints/hash/metadata optional — normalized in the constructor
 * (`parseConstrainedBasis` + {@link Material.updateHash}; `metadata` defaults to `{}`).
 */
export type MaterialConfig<S extends MaterialEnhancedHashedSchema = MaterialEnhancedHashedSchema> =
    Omit<PartialBy<S, "name" | "metadata" | "hash" | "scaledHash">, "basis"> & {
        basis: MaterialSchema["basis"] | MaterialEnhancedSchema["basis"];
    };

export const defaultMaterialConfig: MaterialEnhancedSchema = {
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
        constraints: [],
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

interface BaseMaterial<S extends MaterialEnhancedHashedSchema = MaterialEnhancedHashedSchema>
    extends MaterialSchemaMixin,
        NamedEntity,
        Defaultable,
        Required<HasMetadata<S["metadata"]>> {}

class BaseMaterial<
    S extends MaterialEnhancedHashedSchema = MaterialEnhancedHashedSchema,
> extends InMemoryEntity<S> {}

materialSchemaMixin(BaseMaterial.prototype);
namedEntityMixin(BaseMaterial.prototype);
defaultableEntityMixin(BaseMaterial);
hasMetadataMixin(BaseMaterial.prototype);

/**
 * Unified material. Pass extended schemas via {@link MaterialSchemaMap} so each
 * `toJSON*` returns the web-app (or other host) schema type.
 *
 * @example
 * ```ts
 * type WebappSchemas = {
 *   pure: MaterialSchema;
 *   enhanced: WebappMaterialEnhancedSchema;
 *   hashed: WebappMaterialHashedSchema;
 *   enhancedHashed: WebappMaterialEnhancedSchema;
 * };
 * class CoreMaterial extends Material<WebappSchemas> {}
 * ```
 */
class Material<Schemas extends MaterialSchemaMap = DefaultMaterialSchemas> extends BaseMaterial<
    Schemas["enhancedHashed"]
> {
    declare static createDefault: () => Material<MaterialSchemaMap>;

    /**
     * Schema used by {@link InMemoryEntity.clean} / {@link toJSON}.
     * Defaults to enhanced+hashed; subclasses / web-app Core* may override.
     */
    static get jsonSchema(): JSONSchema {
        return this.jsonSchemaEnhancedHashed;
    }

    /** Schema for {@link toJSONPure} — override in web-app if the base material schema is extended. */
    static get jsonSchemaPure(): JSONSchema {
        return JSONSchemasInterface.getRequiredSchemaById(MATERIAL_SCHEMA_IDS.pure);
    }

    /** Schema for {@link toJSONEnhanced}. */
    static get jsonSchemaEnhanced(): JSONSchema {
        return JSONSchemasInterface.getRequiredSchemaById(MATERIAL_SCHEMA_IDS.enhanced);
    }

    /** Schema for {@link toJSONHashed}. */
    static get jsonSchemaHashed(): JSONSchema {
        return JSONSchemasInterface.getRequiredSchemaById(MATERIAL_SCHEMA_IDS.hashed);
    }

    /** Schema for {@link toJSONEnhancedHashed}. */
    static get jsonSchemaEnhancedHashed(): JSONSchema {
        return JSONSchemasInterface.getRequiredSchemaById(MATERIAL_SCHEMA_IDS.enhancedHashed);
    }

    static get defaultConfig(): MaterialEnhancedSchema {
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

    /**
     * @param config - Partial entity input. `basis.constraints` / `hash` / `metadata` may be omitted;
     *   constraints and hash are filled here; missing `metadata` becomes `{}`.
     * `NoInfer` keeps `Schemas` from being inferred from the config object literal.
     */
    constructor(config: NoInfer<MaterialConfig>) {
        const basis = parseConstrainedBasis(config.basis);

        super({
            ...config,
            basis,
            name: config.name ?? config.formula ?? "",
            metadata: config.metadata ?? {},
            hash: config.hash ?? "",
        });

        this.formula = config.formula || this.getBasis().formula;
        this.name = this.name || this.formula;
        this.updateHash();
    }

    get hash(): Schemas["enhancedHashed"]["hash"] {
        return this.requiredProp("hash");
    }

    set hash(value: Schemas["enhancedHashed"]["hash"]) {
        this.setProp("hash", value);
    }

    get scaledHash(): Schemas["enhancedHashed"]["scaledHash"] {
        return this.prop("scaledHash");
    }

    set scaledHash(value: Schemas["enhancedHashed"]["scaledHash"]) {
        this.setProp("scaledHash", value);
    }

    /** Recompute and store {@link hash} from the current basis/lattice. */
    updateHash(): void {
        this.hash = this.calculateHash("", false, this.isNonPeriodic);
    }

    // Override schema-mixin accessors so basis/lattice changes keep hash in sync.
    get basis(): Schemas["enhancedHashed"]["basis"] {
        return this.requiredProp("basis");
    }

    set basis(value: Schemas["enhancedHashed"]["basis"]) {
        this.setProp("basis", value);
        this.updateHash();
    }

    get lattice(): Schemas["enhancedHashed"]["lattice"] {
        return this.requiredProp("lattice");
    }

    set lattice(value: Schemas["enhancedHashed"]["lattice"]) {
        this.setProp("lattice", value);
        this.updateHash();
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

    setBasis(basis: BasisConfig | ConstrainedBasisConfig): void;

    setBasis(basis: string, format: "xyz", units?: BasisSchema["units"]): void;

    setBasis(
        textOrObject: string | BasisConfig | ConstrainedBasisConfig,
        format?: "xyz",
        units?: BasisSchema["units"],
    ) {
        this.basis = parseConstrainedBasis(textOrObject, format, units);
        this.unsetFileProps();
        this.updateFormula();
    }

    private setBasisConstraints(constraints: Constraint[]) {
        this.setBasis({
            ...this.basis,
            constraints: constraints.map((constraint) => ({
                id: constraint.id,
                value: constraint.value,
            })),
        });
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
            ...parseConstrainedBasis(this.basis),
            cell: this.getLattice().vectors,
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
    toCrystal() {
        this.setBasis(this.getBasis().toCrystal().toJSON());
    }

    /**
     * Converts current material's basis coordinates to cartesian.
     * No changes if coordinates already cartesian.
     */
    toCartesian() {
        this.setBasis(this.getBasis().toCartesian().toJSON());
    }

    /**
     * Returns material's basis in XYZ format.
     */
    getBasisAsXyz(fractional = false): string {
        return parsers.xyz.fromMaterial(this.toJSONPure(), fractional);
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
        return parsers.espresso.toEspressoFormat(this.toJSONPure());
    }

    /**
     * Returns material in POSCAR format. Pass `true` to ignore original poscar source and re-serialize.
     */
    getAsPOSCAR(ignoreOriginal = false, omitConstraints = false): string {
        // By default return original source if exists
        if (this.src?.extension === "poscar" && !ignoreOriginal) {
            return this.src.text;
        }
        return parsers.poscar.toPoscar(this.toJSONEnhanced(), omitConstraints);
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

        return this.clone(config);
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

    /**
     * Full material JSON: constrained basis + hash fields from live getters.
     * Variants below AJV-clean this payload against the matching ESSE schema.
     * Builds from `_json` (not `super.toJSON`) so we do not pre-clean against
     * {@link Material.jsonSchema} before projecting to a narrower schema.
     */
    private getFullJSON(): Schemas["enhancedHashed"] {
        const fullJSON = {
            ...clone(this._json),
            lattice: this.getLattice().toJSON(),
            basis: this.getBasis().toJSON(),
            isNonPeriodic: this.isNonPeriodic,
            hash: this.hash,
        } as Schemas["enhancedHashed"];
        if (this.scaledHash !== undefined) {
            fullJSON.scaledHash = this.scaledHash;
        }
        return fullJSON;
    }

    /**
     * Clone {@link getFullJSON} and validate/clean against `jsonSchema` via AJV
     * (same path as {@link InMemoryEntity.validateData} / {@link InMemoryEntity.clean}).
     */
    private cleanFullJSONAgainstSchema(jsonSchema: JSONSchema): object {
        try {
            return (this.constructor as typeof Material).validateData(
                deepClone(this.getFullJSON()),
                true,
                jsonSchema,
            );
        } catch (err) {
            // validateData throws EntityError with only the code as message — log details for DevTools.
            if (err instanceof EntityError) {
                console.error("Material.toJSON validation failed", {
                    code: err.code,
                    error: err.details?.error,
                    json: err.details?.json,
                    schema: err.details?.schema,
                });
            }
            throw err;
        }
    }

    toJSONPure(): Schemas["pure"] {
        return this.cleanFullJSONAgainstSchema(
            (this.constructor as typeof Material).jsonSchemaPure,
        ) as Schemas["pure"];
    }

    toJSONEnhanced(): Schemas["enhanced"] {
        return this.cleanFullJSONAgainstSchema(
            (this.constructor as typeof Material).jsonSchemaEnhanced,
        ) as Schemas["enhanced"];
    }

    toJSONHashed(): Schemas["hashed"] {
        return this.cleanFullJSONAgainstSchema(
            (this.constructor as typeof Material).jsonSchemaHashed,
        ) as Schemas["hashed"];
    }

    toJSONEnhancedHashed(): Schemas["enhancedHashed"] {
        return this.cleanFullJSONAgainstSchema(
            (this.constructor as typeof Material).jsonSchemaEnhancedHashed,
        ) as Schemas["enhancedHashed"];
    }

    toJSON(): Schemas["enhancedHashed"] {
        // Same payload as toJSONEnhancedHashed when jsonSchema is the enhanced-hashed default.
        return this.cleanFullJSONAgainstSchema(
            (this.constructor as typeof Material).jsonSchema,
        ) as Schemas["enhancedHashed"];
    }
}

export default Material;
