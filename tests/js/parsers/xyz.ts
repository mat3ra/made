import { Utils } from "@mat3ra/utils";
import { expect } from "chai";

import { BasisWithAtomicProperties } from "../../../src/js/basis/basis_with_atomic_properties";
import parsers from "../../../src/js/parsers/parsers";
import { FeO, Silicon } from "../fixtures";

const { assertDeepAlmostEqual } = Utils.assertion;

describe("Parsers:XYZ", () => {
    it("should extract basis from XYZ text", () => {
        const text = "Si 0 0 0 \n Si 0.25 0.25 0.25";
        assertDeepAlmostEqual(
            parsers.xyz.toBasisConfig(text),
            { ...Silicon.basis, units: "cartesian" },
            ["atomic_properties", "cell"],
        );
    });

    it("should extract basis from XYZ text with atomic labels", () => {
        const text =
            "Fe1  0.00  0.00  0.00  1 1 1\n" +
            "Fe2  0.50  0.50  0.50  1 1 1\n" +
            "O    0.25  0.25  0.25  1 1 1\n" +
            "O    0.75  0.75  0.75  1 1 1";
        assertDeepAlmostEqual(parsers.xyz.toBasisConfig(text), FeO.basis, ["cell", "units"]);
    });

    it("should keep atomic labels 0, 1 and 10 from XYZ text to basis and back", () => {
        const text = "Si0 0 0 0\nSi1 0.25 0.25 0.25\nSi10 0.5 0.5 0.5";
        expect(() => parsers.xyz.validate(text)).not.to.throw();
        const basis = new BasisWithAtomicProperties(parsers.xyz.toBasisConfig(text));
        expect(basis.atomicLabelsArray).to.be.deep.equal([0, 1, 10]);
        const xyz = parsers.xyz.fromBasis(basis, "%11.6f");
        expect(xyz.match(/^\S+/gm)).to.be.deep.equal(["Si0", "Si1", "Si10"]);
    });

    it("should return [true, true, true] as constraints for the line without any constraints", () => {
        const text = "Si 0 0 0 0 1 1\n Si 0.25 0.25 0.25";
        const basis = new BasisWithAtomicProperties(parsers.xyz.toBasisConfig(text));
        assertDeepAlmostEqual(basis.constraints.values, [
            [false, true, true],
            [true, true, true],
        ]);
    });
});
