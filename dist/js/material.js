"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Material = exports.defaultMaterialConfig = void 0;
const entity_1 = require("@mat3ra/code/dist/js/entity");
const DefaultableMixin_1 = require("@mat3ra/code/dist/js/entity/mixins/DefaultableMixin");
const HasMetadataMixin_1 = require("@mat3ra/code/dist/js/entity/mixins/HasMetadataMixin");
const NamedEntityMixin_1 = require("@mat3ra/code/dist/js/entity/mixins/NamedEntityMixin");
const crypto_js_1 = __importDefault(require("crypto-js"));
const constrained_basis_1 = require("./basis/constrained_basis");
const conventional_cell_1 = require("./cell/conventional_cell");
const MaterialSchemaMixin_1 = require("./generated/MaterialSchemaMixin");
const lattice_1 = require("./lattice/lattice");
const parsers_1 = __importDefault(require("./parsers/parsers"));
const supercell_1 = __importDefault(require("./tools/supercell"));
function parseBasis(textOrObject, format, unitz) {
    if (typeof textOrObject === "string") {
        if (format !== "xyz") {
            throw new Error("Invalid format");
        }
        return parsers_1.default.xyz.toBasisConfig(textOrObject, unitz);
    }
    return { constraints: [], ...textOrObject };
}
exports.defaultMaterialConfig = {
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
class BaseMaterial extends entity_1.InMemoryEntity {
}
(0, MaterialSchemaMixin_1.materialSchemaMixin)(BaseMaterial.prototype);
(0, NamedEntityMixin_1.namedEntityMixin)(BaseMaterial.prototype);
(0, DefaultableMixin_1.defaultableEntityMixin)(BaseMaterial);
(0, HasMetadataMixin_1.hasMetadataMixin)(BaseMaterial.prototype);
class Material extends BaseMaterial {
    static get defaultConfig() {
        return exports.defaultMaterialConfig;
    }
    static constructMaterialFileSource(fileName, fileContent, fileExtension) {
        return {
            extension: fileExtension,
            filename: fileName,
            text: fileContent,
            hash: crypto_js_1.default.MD5(fileContent).toString(),
        };
    }
    constructor(config, constraints = []) {
        var _a, _b, _c, _d;
        super({
            ...config,
            formula: (_a = config.formula) !== null && _a !== void 0 ? _a : "",
            name: (_c = (_b = config.name) !== null && _b !== void 0 ? _b : config.formula) !== null && _c !== void 0 ? _c : "",
            metadata: (_d = config.metadata) !== null && _d !== void 0 ? _d : {},
        });
        this.constraints = [];
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
    getDerivedPropertyByName(name) {
        return this.getDerivedProperties().find((x) => x.name === name);
    }
    /**
     * @summary Returns the derived properties array for a material.
     */
    getDerivedProperties() {
        var _a;
        return (_a = this.derivedProperties) !== null && _a !== void 0 ? _a : [];
    }
    unsetFileProps() {
        this.unsetProp("src");
        this.unsetProp("icsdId");
        this.unsetProp("external");
    }
    setBasis(textOrObject, format, unitz) {
        const { constraints, ...basis } = parseBasis(textOrObject, format, unitz);
        this.basis = basis;
        this.constraints = constraints;
        this.unsetFileProps();
        this.updateFormula();
    }
    getBasis(constraints) {
        const basisData = this.basis;
        return new constrained_basis_1.ConstrainedBasis({
            ...basisData,
            cell: this.getLattice().vectors,
            constraints: constraints !== null && constraints !== void 0 ? constraints : this.constraints,
        });
    }
    setLattice(lattice) {
        const basis = this.getBasis();
        const originalIsInCrystalUnits = basis.isInCrystalUnits;
        basis.toCartesian();
        basis.cell = new lattice_1.Lattice(lattice).vectors;
        if (originalIsInCrystalUnits) {
            basis.toCrystal();
        }
        this.basis = basis.toJSON();
        this.lattice = lattice;
        this.unsetFileProps();
    }
    getLattice() {
        return new lattice_1.Lattice(this.lattice);
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
    getInchiStringForHash() {
        const inchi = this.getDerivedPropertyByName("inchi");
        if (inchi) {
            return inchi.value;
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
    calculateHash(salt = "", isScaled = false, bypassNonPeriodicCheck = false) {
        let message;
        if (!this.isNonPeriodic || bypassNonPeriodicCheck) {
            message =
                this.getBasis().hashString +
                    "#" +
                    this.getLattice().getHashString(isScaled) +
                    "#" +
                    salt;
        }
        else {
            message = this.getInchiStringForHash();
        }
        return crypto_js_1.default.MD5(message).toString();
    }
    /**
     * Converts basis to crystal/fractional coordinates.
     */
    toCrystal(constraints = []) {
        this.basis = this.getBasis(constraints).toCrystal().toJSON();
    }
    /**
     * Converts current material's basis coordinates to cartesian.
     * No changes if coordinates already cartesian.
     */
    toCartesian(constraints = []) {
        this.basis = this.getBasis(constraints).toCartesian().toJSON();
    }
    /**
     * Returns material's basis in XYZ format.
     */
    getBasisAsXyz(fractional = false) {
        return parsers_1.default.xyz.fromMaterial(this.toJSON(), fractional);
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
    getAsQEFormat() {
        return parsers_1.default.espresso.toEspressoFormat(this.toJSON());
    }
    /**
     * Returns material in POSCAR format. Pass `true` to ignore original poscar source and re-serialize.
     */
    getAsPOSCAR(ignoreOriginal = false, omitConstraints = false) {
        var _a;
        // By default return original source if exists
        if (((_a = this.src) === null || _a === void 0 ? void 0 : _a.extension) === "poscar" && !ignoreOriginal) {
            return this.src.text;
        }
        return parsers_1.default.poscar.toPoscar(this.toJSON(), omitConstraints);
    }
    /**
     * Returns a copy of the material with conventional cell constructed instead of primitive.
     */
    getACopyWithConventionalCell() {
        const material = this.clone();
        const lattice = this.getLattice();
        // if conventional and primitive cells are the same => return a copy.
        if ((0, conventional_cell_1.isConventionalCellSameAsPrimitiveForLatticeType)(lattice.type)) {
            return material;
        }
        const conventionalSupercellMatrix = conventional_cell_1.PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS[lattice.type];
        const conventionalLatticeType = conventional_cell_1.PRIMITIVE_TO_CONVENTIONAL_CELL_LATTICE_TYPES[lattice.type];
        const config = supercell_1.default.generateConfig(this, conventionalSupercellMatrix);
        config.lattice.type = conventionalLatticeType;
        config.name = `${this.name} - conventional cell`;
        // @ts-expect-error
        return new this.constructor(config);
    }
    /**
     * @summary a series of checks for the material and returns an array of results in ConsistencyChecks format.
     * @returns Array of checks results
     */
    getConsistencyChecks() {
        const basisChecks = this.getBasisConsistencyChecks();
        // any other Material checks can be added here
        return basisChecks;
    }
    /**
     * @summary a series of checks for the material's basis and returns an array of results in ConsistencyChecks format.
     * @returns Array of checks results
     */
    getBasisConsistencyChecks() {
        const checks = [];
        const limit = 1000;
        const basis = this.getBasis();
        if (basis.elements.length < limit) {
            const overlappingAtomsGroups = basis.getOverlappingAtoms();
            overlappingAtomsGroups.forEach(({ id1, id2, element1, element2 }) => {
                checks.push({
                    key: `basis.coordinates.${id1}`,
                    name: "atomsOverlap",
                    severity: "warning",
                    message: `Atom ${element1} is too close to ${element2} at position ${id2 + 1}`,
                }, {
                    key: `basis.coordinates.${id2}`,
                    name: "atomsOverlap",
                    severity: "warning",
                    message: `Atom ${element2} is too close to ${element1} at position ${id1 + 1}`,
                });
            });
        }
        return checks;
    }
    toJSON() {
        const lattice = this.getLattice();
        const basis = this.getBasis();
        return {
            ...super.toJSON(),
            lattice: lattice.toJSON(),
            basis: basis.toJSON(),
            isNonPeriodic: this.isNonPeriodic,
        };
    }
}
exports.Material = Material;
