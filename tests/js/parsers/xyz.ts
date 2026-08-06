import { Utils } from "@mat3ra/utils";

import parsers from "../../../src/js/parsers/parsers";
import { FeO, Silicon } from "../fixtures";

const { assertDeepAlmostEqual } = Utils.assertion;

describe("Parsers:XYZ", () => {
    it("should extract basis from XYZ text", () => {
        const text = "Si 0 0 0 \n Si 0.25 0.25 0.25";
        assertDeepAlmostEqual(parsers.xyz.toBasisConfig(text), Silicon.basis, [
            "constraints",
            "cell",
            "units",
        ]);
    });

    it("should extract basis from XYZ text with atomic labels", () => {
        const text =
            "Fe1  0.00  0.00  0.00  1 1 1\n" +
            "Fe2  0.50  0.50  0.50  1 1 1\n" +
            "O    0.25  0.25  0.25  1 1 1\n" +
            "O    0.75  0.75  0.75  1 1 1";
        assertDeepAlmostEqual(parsers.xyz.toBasisConfig(text), FeO.basis, ["cell", "units"]);
    });

    it("should return [true, true, true] as constraints for the line without any constraints", () => {
        const text = "Si 0 0 0 0 1 1\n Si 0.25 0.25 0.25";
        const basis = parsers.xyz.toBasisConfig(text);
        assertDeepAlmostEqual(basis.constraints[0].value, [false, true, true]);
        assertDeepAlmostEqual(basis.constraints[1].value, [true, true, true]);
    });
});
