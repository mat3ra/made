import { expect } from "chai";

import Material from "../../../src/js/Material";
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

    describe("toJSON variants", () => {
        const material = new Material(Silicon);

        it("toJSONPure omits hash and basis.constraints", () => {
            const json = material.toJSONPure();
            expect(json).to.not.have.property("hash");
            expect(json).to.not.have.property("scaledHash");
            expect(json.basis).to.not.have.property("constraints");
            expect(json.name).to.equal(Silicon.name);
        });

        it("toJSONConstrained includes basis.constraints and omits hash", () => {
            const json = material.toJSONConstrained();
            expect(json).to.not.have.property("hash");
            expect(json).to.not.have.property("scaledHash");
            expect(json.basis).to.have.property("constraints").that.is.an("array");
        });

        it("toJSONHashed includes hash and omits basis.constraints", () => {
            const json = material.toJSONHashed();
            expect(json.hash).to.be.a("string");
            expect(json.hash.length).to.be.greaterThan(0);
            expect(json.basis).to.not.have.property("constraints");
        });

        it("toJSONConstrainedHashed includes hash and basis.constraints", () => {
            const json = material.toJSONConstrainedHashed();
            expect(json.hash).to.be.a("string");
            expect(json.hash.length).to.be.greaterThan(0);
            expect(json.basis.constraints).to.be.an("array");
        });

        it("toJSON equals toJSONConstrainedHashed", () => {
            expect(material.toJSON()).to.deep.equal(material.toJSONConstrainedHashed());
        });
    });

    describe("calculateHash", () => {
        [
            { name: "Silicon", fixture: Silicon },
            { name: "Graphene", fixture: Graphene },
        ].forEach(({ name, fixture }) => {
            it(`should match expected hash for ${name}`, () => {
                const material = new Material(fixture);
                expect(material.calculateHash()).to.equal(fixture.hash);
                expect(material.scaledHash).to.equal(fixture.scaledHash);
            });
        });

        it("should match expected hash for FeO (standata)", () => {
            // eslint-disable-next-line global-require, @typescript-eslint/no-var-requires
            const expectedHashes = require("../../fixtures/hashes.json");
            const material = new Material(FeOStandata);
            expect(material.calculateHash()).to.equal(expectedHashes.FeO.hash);
            // scaledHash is stored on schema; standata config may omit it — match main's computed getter.
            expect(material.calculateHash("", true)).to.equal(expectedHashes.FeO.scaledHash);
        });
    });
});
