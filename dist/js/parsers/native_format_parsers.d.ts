import type { MaterialConfig, MaterialConstrainedConfig } from "../Material";
/**
 * @summary Detects the format of the input string
 * @throws If the input string is unknown format
 * @param text input string to detect format
 * @returns Format of the input string
 */
declare function detectFormat(text: string): "json" | "poscar" | "unknown";
/**
 * @summary Function to handle conversion from native formats
 * @param text - input string to detect format and convert
 * @throws If the input string is of unknown format
 * @return Material config
 */
declare function convertFromNativeFormat(text: string): MaterialConfig | MaterialConstrainedConfig;
declare const _default: {
    detectFormat: typeof detectFormat;
    convertFromNativeFormat: typeof convertFromNativeFormat;
};
export default _default;
