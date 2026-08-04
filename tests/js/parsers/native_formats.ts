import "../setup";

import { Utils } from "@mat3ra/utils";
import { expect } from "chai";

import nativeFormatParsers from "../../../src/js/parsers/native_format_parsers";
import { Graphene, GrapheneConstraints, GraphenePoscar, NiHex, NiHexPoscar } from "../fixtures";

const { assertDeepAlmostEqual } = Utils.assertion;

describe("Parsers.NativeFormat", () => {
    it("should return a material config for graphene from a json", () => {
        const json = JSON.stringify(Graphene);
        expect(nativeFormatParsers.convertFromNativeFormat(json)).to.deep.equal(Graphene);
    });

    it("should return a material config for graphene from a poscar", () => {
        const parsedMaterial = nativeFormatParsers.convertFromNativeFormat(GraphenePoscar);
        if (!("constraints" in parsedMaterial.basis)) {
            throw new Error("Expected constrained basis");
        }
        const { constraints, ...basis } = parsedMaterial.basis;
        const config = { ...parsedMaterial, basis };

        assertDeepAlmostEqual(config, Graphene, ["basis.labels", "lattice"]);
        assertDeepAlmostEqual(config.lattice, Graphene.lattice, ["type"]);
        expect(constraints).to.deep.equal(GrapheneConstraints);
    });

    it("should return a material config for Ni hex from a poscar", () => {
        const parsedMaterial = nativeFormatParsers.convertFromNativeFormat(NiHexPoscar);
        if (!("constraints" in parsedMaterial.basis)) {
            throw new Error("Expected constrained basis");
        }
        const { constraints, ...basis } = parsedMaterial.basis;
        const config = { ...parsedMaterial, basis };

        assertDeepAlmostEqual(config, NiHex, ["lattice", "basis.labels"]);
        assertDeepAlmostEqual(config.lattice, NiHex.lattice, ["type"]);
        expect(constraints).to.deep.equal([]);
    });

    it("should throw an error for unknown format", () => {
        const text = "A\n snippet from an unknown format";
        expect(() => nativeFormatParsers.convertFromNativeFormat(text)).to.throw("Unknown format");
    });
});
