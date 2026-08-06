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
exports.defaultMaterialConstrainedHashedConfig = void 0;
const MaterialConstrained_1 = __importStar(require("./MaterialConstrained"));
const MaterialHashedMixin_1 = require("./mixins/MaterialHashedMixin");
exports.defaultMaterialConstrainedHashedConfig = {
    ...MaterialConstrained_1.defaultMaterialConstrainedConfig,
    hash: "",
};
class MaterialConstrainedHashed extends MaterialConstrained_1.default {
    static get defaultConfig() {
        return exports.defaultMaterialConstrainedHashedConfig;
    }
    static fromMaterial(material) {
        const constraints = "constraints" in material.basis ? material.basis.constraints : [];
        return new MaterialConstrainedHashed({
            ...material.toJSON(),
            basis: {
                ...material.basis,
                constraints,
            },
            hash: material.calculateHash("", false, material.isNonPeriodic),
        });
    }
    constructor(config) {
        super(config);
        this.hash = config.hash || this.calculateHash("", false, this.isNonPeriodic);
    }
}
(0, MaterialHashedMixin_1.materialHashedMixin)(MaterialConstrainedHashed.prototype);
exports.default = MaterialConstrainedHashed;
