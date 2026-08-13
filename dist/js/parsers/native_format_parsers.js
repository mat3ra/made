"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const poscar_1 = __importDefault(require("./poscar"));
const NATIVE_FORMAT = {
    JSON: "json",
    POSCAR: "poscar",
    CIF: "cif",
    PWX: "pwx",
    XYZ: "xyz",
    UNKNOWN: "unknown",
};
/**
 * @summary Detects the format of the input string
 * @throws If the input string is unknown format
 * @param text input string to detect format
 * @returns Format of the input string
 */
function detectFormat(text) {
    const jsonRegex = /^\s*\{/;
    if (jsonRegex.test(text))
        return NATIVE_FORMAT.JSON;
    if (poscar_1.default.isPoscar(text))
        return NATIVE_FORMAT.POSCAR;
    return NATIVE_FORMAT.UNKNOWN;
}
/**
 * @summary Function to handle conversion from native formats
 * @param text - input string to detect format and convert
 * @throws If the input string is of unknown format
 * @return Material config
 */
function convertFromNativeFormat(text) {
    const format = detectFormat(text);
    switch (format) {
        case NATIVE_FORMAT.JSON:
            return JSON.parse(text);
        case NATIVE_FORMAT.POSCAR:
            return poscar_1.default.fromPoscar(text);
        case NATIVE_FORMAT.UNKNOWN:
            throw new Error(`Unknown format`);
        // TODO:  add more formats
        default:
            throw new Error(`Unsupported format: ${format}`);
    }
}
exports.default = {
    detectFormat,
    convertFromNativeFormat,
};
