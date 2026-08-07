import { MaterialEnhancedSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";
/**
 * Construct textual representation of a materialOrConfig according to Quantum ESPRESSO pw.x input format.
 */
declare function toEspressoFormat(materialOrConfig: MaterialSchema | MaterialEnhancedSchema): string;
declare const _default: {
    toEspressoFormat: typeof toEspressoFormat;
};
export default _default;
