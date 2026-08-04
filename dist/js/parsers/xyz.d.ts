import { MaterialConstrainedSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";
import { ConstrainedBasis, ConstrainedBasisConfig } from "../basis/constrained_basis";
import { AtomicCoordinateValue } from "../basis/coordinates";
import { AtomicElementValue } from "../basis/elements";
import { Cell } from "../cell/cell";
import { AtomicConstraintValue } from "../constraints/constraints";
import { CombinatorialBasis } from "./xyz_combinatorial_basis";
export declare const XYZ_COORDINATE_PRECISION = 4;
/**
 * Validates that passed string is well-formed XYZ file.
 */
export declare function validate(xyzTxt: string): void;
export interface ParsedObject {
    element: AtomicElementValue;
    coordinate: AtomicCoordinateValue;
    constraints: AtomicConstraintValue;
    label?: number;
}
/**
 * Parse XYZ text for basis.
 * @param txt Text
 * @param units Coordinate units
 * @param cell Basis Cell
 */
declare function toBasisConfig(txt: string, units?: string, cell?: Cell): ConstrainedBasisConfig;
/**
 * Create XYZ from Basis class instance.
 * @param basisClsInstance Basis class instance.
 * @param coordinatePrintFormat Output format for coordinates.
 * @return Basis string in XYZ format
 */
declare function fromBasis(basisClsInstance: ConstrainedBasis, coordinatePrintFormat: string): string;
/**
 * Create XYZ from Material class instance (or its JSON config).
 * Prefer fromBasis when you already have a ConstrainedBasis instance.
 */
declare function fromMaterial(materialOrConfig: MaterialSchema | MaterialConstrainedSchema, fractional?: boolean): string;
declare const _default: {
    validate: typeof validate;
    fromMaterial: typeof fromMaterial;
    toBasisConfig: typeof toBasisConfig;
    fromBasis: typeof fromBasis;
    CombinatorialBasis: typeof CombinatorialBasis;
};
export default _default;
