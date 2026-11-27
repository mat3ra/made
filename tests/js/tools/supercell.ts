import { Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { expect } from "chai";

import { Basis } from "../../../src/js/basis/basis";
import { Made } from "../../../src/js/made";
import Material from "../../../src/js/Material";
import { SiGeSupercellBasisWithLabelAndConstraint, Silicon, SiSupercell } from "../fixtures";

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

    it("should copy each atom's label and constraint to its supercell copies", () => {
        const newBasisXYZ = `Si1    0.000000    0.000000    0.000000 0 0 1
Ge     0.250000    0.250000    0.250000
`;
        const material = new Material(Silicon);
        const clonedMaterial = material.clone();
        clonedMaterial.setBasis(newBasisXYZ, "xyz", clonedMaterial.getBasis().units);
        const supercellConfig = Made.tools.supercell.generateConfig(clonedMaterial, [
            [2, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ] as Matrix3X3Schema);

        assertDeepAlmostEqual(SiGeSupercellBasisWithLabelAndConstraint, supercellConfig.basis);
    });
});
