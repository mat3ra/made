import { Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Basis } from "../basis/basis";
import { ConstrainedBasis } from "../basis/constrained_basis";
import { Cell } from "../cell/cell";
import type { MaterialSchemaMap } from "../Material";
import type Material from "../Material";
/**
 * @summary Generates new basis for a supercell. For each site from basis generates shifts that are within supercell.
 */
declare function generateNewBasisWithinSupercell(basis: Basis | ConstrainedBasis, cell: Cell, supercell: Cell, supercellMatrix: Matrix3X3Schema): Basis;
/**
 * @summary Generates supercell config for the specified material.
 */
declare function generateConfig<Schemas extends MaterialSchemaMap = MaterialSchemaMap>(material: Material<Schemas>, supercellMatrix: Matrix3X3Schema): {
    name: string;
    basis: import("../basis/basis").BasisConfig & import("@mat3ra/esse/dist/js/types").BaseInMemoryEntitySchema;
    lattice: import("@mat3ra/esse/dist/js/types").LatticeSchema;
};
declare const _default: {
    generateConfig: typeof generateConfig;
    generateNewBasisWithinSupercell: typeof generateNewBasisWithinSupercell;
};
export default _default;
