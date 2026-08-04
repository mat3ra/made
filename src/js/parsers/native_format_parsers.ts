import type { MaterialConfig } from "../Material";
import type { MaterialConstrainedConfig } from "../MaterialConstrained";
import Poscar from "./poscar";

const NATIVE_FORMAT = {
    JSON: "json",
    POSCAR: "poscar",
    CIF: "cif",
    PWX: "pwx",
    XYZ: "xyz",
    UNKNOWN: "unknown",
} as const;

/**
 * @summary Detects the format of the input string
 * @throws If the input string is unknown format
 * @param text input string to detect format
 * @returns Format of the input string
 */
function detectFormat(text: string) {
    const jsonRegex = /^\s*\{/;
    if (jsonRegex.test(text)) return NATIVE_FORMAT.JSON;
    if (Poscar.isPoscar(text)) return NATIVE_FORMAT.POSCAR;

    return NATIVE_FORMAT.UNKNOWN;
}

/**
 * @summary Function to handle conversion from native formats
 * @param text - input string to detect format and convert
 * @throws If the input string is of unknown format
 * @return Material config
 */
function convertFromNativeFormat(text: string): MaterialConfig | MaterialConstrainedConfig {
    const format = detectFormat(text);

    switch (format) {
        case NATIVE_FORMAT.JSON:
            return JSON.parse(text);
        case NATIVE_FORMAT.POSCAR:
            return Poscar.fromPoscar(text);
        case NATIVE_FORMAT.UNKNOWN:
            throw new Error(`Unknown format`);
        // TODO:  add more formats
        default:
            throw new Error(`Unsupported format: ${format}`);
    }
}

export default {
    detectFormat,
    convertFromNativeFormat,
};
