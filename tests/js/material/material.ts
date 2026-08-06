import { expect } from "chai";

import Material from "../../../src/js/Material";
import MaterialHashed from "../../../src/js/MaterialHashed";
import { FeOStandata, Graphene, Na4Cl4, Silicon } from "../fixtures";

const newBasisXYZ = `Si     0.000000    0.000000    0.000000
Ge     0.250000    0.250000    0.250000
`;

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
            // eslint-disable-next-line global-require, @typescript-eslint/no-var-requires
            const expectedHashes = require("../../fixtures/hashes.json");
            const material = new MaterialHashed(FeOStandata);
            expect(material.calculateHash()).to.equal(expectedHashes.FeO.hash);
            // scaledHash is stored on schema; standata config may omit it — match main's computed getter.
            expect(material.calculateHash("", true)).to.equal(expectedHashes.FeO.scaledHash);
        });
    });
});
