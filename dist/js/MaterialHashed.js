"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const HashedSchemaMixin_1 = require("@mat3ra/code/dist/js/generated/HashedSchemaMixin");
const Material_1 = __importStar(require("./Material"));
class MaterialHashed extends Material_1.default {
    static get defaultConfig() {
        return Material_1.defaultMaterialConfig;
    }
    static fromMaterial(material) {
        return new MaterialHashed({
            ...material.toJSON(),
            hash: material.calculateHash("", false, material.isNonPeriodic),
        });
    }
    // NoInfer: keep default S (or an explicit type arg) instead of inferring S from the config literal.
    constructor(config) {
        var _a, _b;
        // MaterialConfig<S> still requires hash; use a placeholder until calculateHash can run.
        super({
            ...config,
            hash: (_a = config.hash) !== null && _a !== void 0 ? _a : "",
        });
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
(0, HashedSchemaMixin_1.hashedSchemaMixin)(MaterialHashed.prototype);
exports.default = MaterialHashed;
