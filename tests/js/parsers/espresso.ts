import { expect } from "chai";

import Material from "../../../src/js/Material";
import parsers from "../../../src/js/parsers/parsers";
import { Silicon, SiPWSCFInput } from "../fixtures";

describe("Parsers:Espresso", () => {
    it("should return textual representation of a material according to QE pw.x input format", () => {
        const material = new Material(Silicon);
        expect(parsers.espresso.toEspressoFormat(material.toJSON())).to.be.equal(SiPWSCFInput);
    });
});
