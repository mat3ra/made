import { expect } from "chai";

import { Material } from "../../src/js/material";
import { FeOStandata, Graphene, Na4Cl4, Silicon } from "./fixtures";

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

    describe("calculateHash", () => {
        [
            { name: "Silicon", fixture: Silicon },
            { name: "Graphene", fixture: Graphene },
        ].forEach(({ name, fixture }) => {
            it(`should match expected hash for ${name}`, () => {
                const material = new Material(fixture);
                expect(material.calculateHash()).to.equal((fixture as any).hash);
                expect(material.scaledHash).to.equal((fixture as any).scaledHash);
            });
        });

        it("should match expected hash for FeO (standata)", () => {
            const expectedHashes = require("../../fixtures/hashes.json");
            const material = new Material(FeOStandata);
            expect(material.calculateHash()).to.equal(expectedHashes.FeO.hash);
            expect(material.scaledHash).to.equal(expectedHashes.FeO.scaledHash);
        });
    });
});
