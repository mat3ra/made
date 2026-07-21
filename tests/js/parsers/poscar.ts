import { expect } from "chai";

import { AtomicConstraints } from "../../../src/js/constraints/constraints";
import { Material } from "../../../src/js/material";
import parsers from "../../../src/js/parsers/parsers";
import { atomsCount } from "../../../src/js/parsers/poscar";
import {
    atomicConstraints,
    H2OPoscar,
    Na4Cl4,
    Na4Cl4Poscar,
    Silicon,
    Zr1H23Zr1H1,
    Zr1H23Zr1H1Poscar,
} from "../fixtures";

const O2_POSCAR_WITH_COMMENTS = `O2 molecule in a box
1.0 ! universal scaling parameters
12.0 0.0 0.0 ! lattice vector a(1)
0.0 12.0 0.0 ! lattice vector a(2)
0.0 0.0 12.0 ! lattice vector a(3)
O
2 ! number of atoms
cart ! positions in cartesian coordinates
0 0 0 O
0 0 1.21 O
`;

describe("Parsers.POSCAR", () => {
    it("should return a valid poscar", () => {
        const material = new Material(Na4Cl4);
        expect(`${material.getAsPOSCAR()}\n`).to.be.equal(Na4Cl4Poscar);
    });

    it("should return poscar elements line according to id in basis, duplicate entries separate", () => {
        const material = new Material(Zr1H23Zr1H1);
        expect(`${material.getAsPOSCAR()}\n`).to.be.equal(Zr1H23Zr1H1Poscar);
    });

    it("should return the number of atoms for a molecule in a poscar file", () => {
        expect(atomsCount(H2OPoscar)).to.be.equal(3);
    });

    it("should detect POSCAR with VASP-style comments", () => {
        expect(parsers.poscar.isPoscar(O2_POSCAR_WITH_COMMENTS)).to.be.equal(true);
        expect(parsers.nativeFormatParsers.detectFormat(O2_POSCAR_WITH_COMMENTS)).to.be.equal(
            "poscar",
        );
    });

    it("should parse POSCAR with VASP-style comments", () => {
        const materialConfig = parsers.poscar.fromPoscar(O2_POSCAR_WITH_COMMENTS);
        expect(materialConfig).to.have.property("basis");
        expect((materialConfig as { basis: { elements: object[] } }).basis.elements).to.have.length(
            2,
        );
    });

    it("should return constraints as string with given map function", () => {
        const constraints = AtomicConstraints.fromObjects(atomicConstraints);
        expect(
            constraints.getAsStringByIndex(0, parsers.poscar.atomicConstraintsCharFromBool),
        ).to.be.equal("T T F");
    });

    it("should generate POSCAR with constraints if they were present", () => {
        const newBasisXYZ = `Si     0.000000    0.000000    0.000000 0 0 0
Ge     0.250000    0.250000    0.250000 1 1 1
`;
        const poscarConstraints = `Silicon FCC
1.0
   3.348920000\t   0.000000000\t   1.933500000
   1.116307000\t   3.157392000\t   1.933500000
   0.000000000\t   0.000000000\t   3.867000000
Si Ge
1 1
Selective dynamics
direct
   0.000000000    0.000000000    0.000000000 F F F Si
   0.250000000    0.250000000    0.250000000 T T T Ge`;

        const material = new Material(Silicon);
        const clonedMaterial = material.clone();
        clonedMaterial.setBasis(newBasisXYZ, "xyz", clonedMaterial.getBasis().units);

        const poscar = clonedMaterial.getAsPOSCAR(true);
        expect(poscar).to.be.equal(poscarConstraints);
    });
});
