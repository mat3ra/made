import { AtomicConstraintsSchema } from "@mat3ra/esse/dist/js/types";
import { expect } from "chai";

import { AtomicConstraints } from "../../../src/js/constraints/constraints";
import { atomicConstraints } from "../fixtures";

describe("AtomicConstraints", () => {
    it("should return constraints as string", () => {
        const constraints = AtomicConstraints.fromObjects(atomicConstraints);
        expect(constraints.getAsStringByIndex(0)).to.be.equal("1 1 0");
    });

    it("should return constraints as ESSE JSON", () => {
        const json: AtomicConstraintsSchema =
            AtomicConstraints.fromObjects(atomicConstraints).toJSON();
        expect(json).to.deep.equal(atomicConstraints);
    });
});
