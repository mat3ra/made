import type { MaterialConstrainedSchema, MaterialHashedSchema } from "@mat3ra/esse/dist/js/types";
import { expect } from "chai";

import Material from "../../src/js/Material";
import MaterialConstrained from "../../src/js/MaterialConstrained";
import MaterialConstrainedHashed from "../../src/js/MaterialConstrainedHashed";
import MaterialHashed from "../../src/js/MaterialHashed";
import expectedHashes from "../fixtures/hashes.json";
import { FeOStandata, Graphene, Na4Cl4, Silicon } from "./fixtures";

const newBasisXYZ = `Si     0.000000    0.000000    0.000000
Ge     0.250000    0.250000    0.250000
`;

const constrainedSilicon: MaterialConstrainedSchema = {
    ...Silicon,
    basis: {
        ...Silicon.basis,
        constraints: [],
    },
};

describe("Material", () => {
    it("should return unique elements", () => {
        const material = new Material(Na4Cl4);
        expect(material.uniqueElements).to.have.same.members(["Na", "Cl"]);
    });

    it("should return cloned material", () => {
        const material = new Material(Silicon);
        const clonedMaterial = material.clone();
        clonedMaterial.setBasis(newBasisXYZ, "xyz", clonedMaterial.getBasis().units);
        expect(clonedMaterial.getBasis().elements).to.have.lengthOf(2);
    });

    describe("atomic constraints", () => {
        const constrainedBasisXYZ = `Li 0 0 0 1 1 0
Li 0.25 0.25 0.25
`;

        it("does not retain constraints parsed from XYZ", () => {
            const material = new Material(Silicon);
            material.setBasis(constrainedBasisXYZ, "xyz", "crystal");

            expect(material.basis).to.not.have.property("constraints");
            expect(material.toJSON().basis).to.not.have.property("constraints");
            expect(material.getAsPOSCAR(true)).to.not.include("Selective dynamics");
        });
    });
});

describe("MaterialConstrained", () => {
    const constrainedBasisXYZ = `Li 0 0 0 1 1 0
Li 0.25 0.25 0.25
`;

    it("stores parsed constraints in basis JSON", () => {
        const material = new MaterialConstrained(constrainedSilicon);
        material.setBasis(constrainedBasisXYZ, "xyz", "crystal");

        expect(material.basis.constraints).to.deep.equal([
            { id: 0, value: [true, true, false] },
            { id: 1, value: [true, true, true] },
        ]);
        expect(material.toJSON().basis.constraints).to.deep.equal(material.basis.constraints);
        expect(material.getBasisAsXyz()).to.include("1 1 0");
    });

    it("preserves basis constraints across clone and lattice changes", () => {
        const material = new MaterialConstrained(constrainedSilicon);
        material.setBasis(constrainedBasisXYZ, "xyz", "crystal");
        const cloned = material.clone();

        cloned.setLattice({ ...cloned.lattice, a: cloned.lattice.a + 0.1 });

        expect(cloned.basis.constraints).to.deep.equal(material.basis.constraints);
    });

    it("serializes embedded constraints to POSCAR", () => {
        const material = new MaterialConstrained(constrainedSilicon);
        material.setBasis(constrainedBasisXYZ, "xyz", "crystal");
        const poscar = material.getAsPOSCAR(true);

        expect(poscar).to.include("Selective dynamics");
        expect(poscar).to.match(/T\s+T\s+F/);
    });
});

describe("MaterialHashed", () => {
    describe("calculateHash", () => {
        [
            { name: "Silicon", fixture: Silicon },
            { name: "Graphene", fixture: Graphene },
        ].forEach(({ name, fixture }) => {
            it(`should match expected hash for ${name}`, () => {
                const material = new MaterialHashed(fixture);
                expect(material.calculateHash()).to.equal(fixture.hash);
                expect(material.scaledHash).to.equal(fixture.scaledHash);
            });
        });

        it("should match expected hash for FeO (standata)", () => {
            const material = new MaterialHashed(FeOStandata);
            expect(material.calculateHash()).to.equal(expectedHashes.FeO.hash);
            expect(material.calculateHash("", true)).to.equal(expectedHashes.FeO.scaledHash);
        });

        it("should persist hash on the instance and refresh after mutation", () => {
            const material = new MaterialHashed(Silicon);
            expect(material.hash).to.equal(Silicon.hash);
            material.setBasis(newBasisXYZ, "xyz", material.getBasis().units);
            expect(material.hash).to.equal(material.calculateHash());
            expect(material.hash).to.not.equal(Silicon.hash);
        });

        it("should refresh hash when basis or lattice setters are used directly", () => {
            const material = new MaterialHashed(Silicon);
            const previousHash = material.hash;

            material.basis = {
                ...material.basis,
                elements: [
                    { id: 0, value: "Si" },
                    { id: 1, value: "Ge" },
                ],
            };
            expect(material.hash).to.equal(material.calculateHash());
            expect(material.hash).to.not.equal(previousHash);

            const hashAfterBasisChange = material.hash;
            material.lattice = {
                ...material.lattice,
                a: material.lattice.a + 0.1,
            };
            expect(material.hash).to.equal(material.calculateHash());
            expect(material.hash).to.not.equal(hashAfterBasisChange);
        });

        it("should refresh hash after setLattice", () => {
            const material = new MaterialHashed(Silicon);
            const previousHash = material.hash;

            material.setLattice({
                ...material.lattice,
                a: material.lattice.a + 0.1,
            });
            expect(material.hash).to.equal(material.calculateHash());
            expect(material.hash).to.not.equal(previousHash);
        });
    });

    describe("generic schema wrapper", () => {
        type WiderMaterialHashedSchema = MaterialHashedSchema & { webappOnly?: string };

        class WiderMaterialHashed extends MaterialHashed<WiderMaterialHashedSchema> {}

        it("allows subclasses to widen _json typing and storage", () => {
            const material = new WiderMaterialHashed(Silicon);

            material._json.webappOnly = "webapp-value";
            expect(material._json.webappOnly).to.equal("webapp-value");

            // toJSON rebuilds from schema-shaped fields; _json retains widened keys.
            expect(material.toJSON().name).to.equal(Silicon.name);
            expect(material._json.webappOnly).to.equal("webapp-value");

            material._json.webappOnly = "updated";
            expect(material._json.webappOnly).to.equal("updated");
        });
    });
});

describe("MaterialConstrainedHashed", () => {
    it("stores constraints in basis and refreshes hash after basis mutation", () => {
        const material = new MaterialConstrainedHashed({
            ...constrainedSilicon,
            hash: Silicon.hash,
        });
        const previousHash = material.hash;

        material.setBasis(
            `Si 0 0 0 1 1 0
Ge 0.25 0.25 0.25 1 1 1
`,
            "xyz",
            "crystal",
        );

        expect(material.basis.constraints).to.have.lengthOf(2);
        expect(material.hash).to.equal(material.calculateHash());
        expect(material.hash).to.not.equal(previousHash);
    });
});
