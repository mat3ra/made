import { AtomicConstraintsSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";
/**
 * Construct textual representation of a materialOrConfig according to Quantum ESPRESSO pw.x input format.
 * Constraints are not part of ESSE basis — pass them separately.
 */
declare function toEspressoFormat(materialOrConfig: MaterialSchema, constraints?: AtomicConstraintsSchema): string;
declare const _default: {
    toEspressoFormat: typeof toEspressoFormat;
};
export default _default;
