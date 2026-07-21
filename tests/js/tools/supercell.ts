import { Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { expect } from "chai";

import { Basis } from "../../../src/js/basis/basis";
import { Made } from "../../../src/js/made";
import { Material } from "../../../src/js/material";
import { Silicon, SiSupercell } from "../fixtures";

const { assertDeepAlmostEqual } = Utils.assertion;

describe("Tools:Supercell", () => {
    it("should generate supercell", () => {
        const material = new Material(Silicon);
        const supercell = Made.tools.supercell.generateConfig(material, [
            [2, 0, 0],
            [0, 2, 0],
            [0, 0, 2],
        ] as Matrix3X3Schema);
        // expect(supercell.lattice).deep.equal(SiSupercell.lattice, "lattices are not equal");
        assertDeepAlmostEqual(supercell.lattice, SiSupercell.lattice, ["vectors"]);

        const basis1 = new Basis(SiSupercell.basis);
        const basis2 = new Basis(supercell.basis);

        expect(basis1.isEqualTo(basis2)).to.be.equal(true);
    });

    it("should generate supercell with removed constraints", () => {
        const newBasisXYZ = `Si     0.000000    0.000000    0.000000
Ge     0.250000    0.250000    0.250000
`;
        const poscarNoConstraints = `Silicon FCC - supercell [[2,0,0],[0,1,0],[0,0,1]]
1.0
   6.697840000\t   0.000000000\t   3.867000000
   1.116307000\t   3.157392000\t   1.933500000
   0.000000000\t   0.000000000\t   3.867000000
Si Ge
2 2
direct
   0.000000000    0.000000000    0.000000000  Si
   0.500000000    0.000000000    0.000000000  Si
   0.125000000    0.250000000    0.250000000  Ge
   0.625000000    0.250000000    0.250000000  Ge`;
        const material = new Material(Silicon);
        const clonedMaterial = material.clone();
        clonedMaterial.setBasis(newBasisXYZ, "xyz", clonedMaterial.getBasis().units);
        const supercellConfig = Made.tools.supercell.generateConfig(clonedMaterial, [
            [2, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ] as Matrix3X3Schema);

        const newMaterial = new Material(supercellConfig);
        const poscar = newMaterial.getAsPOSCAR(true);
        expect(poscar).to.be.equal(poscarNoConstraints);
    });
});
