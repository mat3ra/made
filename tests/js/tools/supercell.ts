import { Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { expect } from "chai";

import { ProtoPropertyEnum } from "../../../src/js/basis/atomic_properties";
import { Basis } from "../../../src/js/basis/basis";
import { Made } from "../../../src/js/made";
import Material from "../../../src/js/Material";
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

    it("should copy each atom's label and constraint to its supercell copies", () => {
        const newBasisXYZ = `Si1    0.000000    0.000000    0.000000 0 0 1
Ge     0.250000    0.250000    0.250000
`;
        const supercellBasis = {
            elements: [
                { id: 0, value: "Si" },
                { id: 1, value: "Si" },
                { id: 2, value: "Ge" },
                { id: 3, value: "Ge" },
            ],
            coordinates: [
                { id: 0, value: [0, 0, 0] },
                { id: 1, value: [0.5, 0, 0] },
                { id: 2, value: [0.125, 0.25, 0.25] },
                { id: 3, value: [0.625, 0.25, 0.25] },
            ],
            units: "crystal",
            atomic_properties: [
                {
                    name: ProtoPropertyEnum.atomic_constraints,
                    values: [
                        { id: 0, value: [false, false, true] },
                        { id: 1, value: [false, false, true] },
                        { id: 2, value: [true, true, true] },
                        { id: 3, value: [true, true, true] },
                    ],
                },
                {
                    name: ProtoPropertyEnum.atomic_labels,
                    values: [
                        { id: 0, value: 1 },
                        { id: 1, value: 1 },
                    ],
                },
            ],
        };
        const supercellPoscar = `Silicon FCC - supercell [[2,0,0],[0,1,0],[0,0,1]]
1.0
   6.697840000\t   0.000000000\t   3.867000000
   1.116307000\t   3.157392000\t   1.933500000
   0.000000000\t   0.000000000\t   3.867000000
Si Ge
2 2
Selective dynamics
direct
   0.000000000    0.000000000    0.000000000 F F T Si
   0.500000000    0.000000000    0.000000000 F F T Si
   0.125000000    0.250000000    0.250000000 T T T Ge
   0.625000000    0.250000000    0.250000000 T T T Ge`;
        const material = new Material(Silicon);
        const clonedMaterial = material.clone();
        clonedMaterial.setBasis(newBasisXYZ, "xyz", clonedMaterial.getBasis().units);
        const supercellConfig = Made.tools.supercell.generateConfig(clonedMaterial, [
            [2, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ] as Matrix3X3Schema);

        assertDeepAlmostEqual(supercellBasis, supercellConfig.basis);
        expect(new Material(supercellConfig).getAsPOSCAR(true)).to.be.equal(supercellPoscar);
    });
});
