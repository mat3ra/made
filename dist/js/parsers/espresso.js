"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const lodash_1 = require("lodash");
const underscore_string_1 = __importDefault(require("underscore.string"));
const lattice_1 = require("../lattice/lattice");
const xyz_1 = __importDefault(require("./xyz"));
/**
 * Construct textual representation of a materialOrConfig according to Quantum ESPRESSO pw.x input format.
 */
function toEspressoFormat(materialOrConfig) {
    const l = new lattice_1.Lattice(materialOrConfig.lattice);
    const vectors = l.vectorArrays;
    const vectorsAsString = (0, lodash_1.map)(vectors, (v) => {
        return `${underscore_string_1.default.sprintf("%14.9f", v[0])}\t${underscore_string_1.default.sprintf("%14.9f", v[1])}\t${underscore_string_1.default.sprintf("%14.9f", v[2])}`;
    }).join("\n");
    return underscore_string_1.default.sprintf("CELL_PARAMETERS (angstroms)\n%s\n\nATOMIC_POSITIONS (crystal)\n%s", vectorsAsString, xyz_1.default.fromMaterial(materialOrConfig));
}
exports.default = {
    toEspressoFormat,
};
