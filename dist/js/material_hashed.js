"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MaterialHashed = void 0;
const HashedSchemaMixin_1 = require("@mat3ra/code/dist/js/generated/HashedSchemaMixin");
const material_1 = require("./material");
class MaterialHashed extends material_1.Material {
    static get defaultConfig() {
        return material_1.defaultMaterialConfig;
    }
    // NoInfer: keep default S (or an explicit type arg) instead of inferring S from the config literal.
    constructor(config, constraints = []) {
        var _a, _b;
        // MaterialConfig<S> still requires hash; use a placeholder until calculateHash can run.
        super({
            ...config,
            hash: (_a = config.hash) !== null && _a !== void 0 ? _a : "",
        }, constraints);
        this.hash = (_b = config.hash) !== null && _b !== void 0 ? _b : this.calculateHash("", false, this.isNonPeriodic);
    }
    get basis() {
        return super.basis;
    }
    set basis(value) {
        super.basis = value;
        this.updateHash();
    }
    get lattice() {
        return super.lattice;
    }
    set lattice(value) {
        super.lattice = value;
        this.updateHash();
    }
    updateHash() {
        this.hash = this.calculateHash("", false, this.isNonPeriodic);
    }
}
exports.MaterialHashed = MaterialHashed;
(0, HashedSchemaMixin_1.hashedSchemaMixin)(MaterialHashed.prototype);
