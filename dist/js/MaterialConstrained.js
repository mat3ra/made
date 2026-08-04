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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.defaultMaterialConstrainedConfig = void 0;
const constrained_basis_1 = require("./basis/constrained_basis");
const constraints_1 = require("./constraints/constraints");
const Material_1 = __importStar(require("./Material"));
const parsers_1 = __importDefault(require("./parsers/parsers"));
exports.defaultMaterialConstrainedConfig = {
    ...Material_1.defaultMaterialConfig,
    basis: {
        ...Material_1.defaultMaterialConfig.basis,
        constraints: [],
    },
};
function parseConstrainedBasis(textOrObject, format, unitz) {
    if (typeof textOrObject === "string") {
        if (format !== "xyz") {
            throw new Error("Invalid format");
        }
        return parsers_1.default.xyz.toBasisConfig(textOrObject, unitz);
    }
    if ("constraints" in textOrObject) {
        return textOrObject;
    }
    return { ...textOrObject, constraints: [] };
}
class MaterialConstrained extends Material_1.default {
    static get defaultConfig() {
        return exports.defaultMaterialConstrainedConfig;
    }
    static fromMaterial(material) {
        const constraints = "constraints" in material.basis ? material.basis.constraints : [];
        return new MaterialConstrained({
            ...material.toJSON(),
            basis: {
                ...material.basis,
                constraints,
            },
        });
    }
    get basis() {
        return this.requiredProp("basis");
    }
    set basis(basis) {
        super.basis = basis;
    }
    setConstrainedBasis(basis) {
        super.basis = basis;
    }
    setBasis(textOrObject, format, unitz) {
        this.setConstrainedBasis(parseConstrainedBasis(textOrObject, format, unitz));
        this.unsetFileProps();
        this.updateFormula();
    }
    setBasisConstraints(constraints) {
        this.basis = {
            ...this.basis,
            constraints: constraints.map((constraint) => ({
                id: constraint.id,
                value: constraint.value,
            })),
        };
        this.unsetFileProps();
    }
    setBasisConstraintsFromArrayOfObjects(constraints) {
        this.setBasisConstraints(constraints.map((constraint) => constraints_1.Constraint.fromValueAndId(constraint.value, constraint.id)));
    }
    getBasis() {
        return new constrained_basis_1.ConstrainedBasis({
            ...this.basis,
            cell: this.getLattice().vectors,
        });
    }
}
exports.default = MaterialConstrained;
