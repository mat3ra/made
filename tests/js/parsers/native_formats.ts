import "../setup";

import { Utils } from "@mat3ra/utils";
import { expect } from "chai";

import nativeFormatParsers from "../../../src/js/parsers/native_format_parsers";
import { Graphene, GraphenePoscar, NiHex, NiHexPoscar } from "../fixtures";

const { assertDeepAlmostEqual } = Utils.assertion;

describe("Parsers.NativeFormat", () => {
    it("should return a material config for graphene from a json", () => {
        const json = JSON.stringify(Graphene);
        expect(nativeFormatParsers.convertFromNativeFormat(json)).to.deep.equal(Graphene);
    });

    it("should return a material config for graphene from a poscar", () => {
        const poscar = GraphenePoscar;
        const config = nativeFormatParsers.convertFromNativeFormat(poscar);
        assertDeepAlmostEqual(config, Graphene, ["basis.labels", "lattice"]);
        assertDeepAlmostEqual(config.lattice, Graphene.lattice, ["type"]);
    });

    it("should return a material config for Ni hex from a poscar", () => {
        const poscar = NiHexPoscar;
        const config = nativeFormatParsers.convertFromNativeFormat(poscar);
        assertDeepAlmostEqual(config, NiHex, ["lattice", "basis.labels"]);
        assertDeepAlmostEqual(config.lattice, NiHex.lattice, ["type"]); // to omit "lattice.type" property
    });

    it("should throw an error for unknown format", () => {
        const text = "A\n snippet from an unknown format";
        expect(() => nativeFormatParsers.convertFromNativeFormat(text)).to.throw("Unknown format");
    });
});
