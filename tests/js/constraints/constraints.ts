import { expect } from "chai";

import { AtomicConstraints } from "../../../src/js/constraints/constraints";
import { atomicConstraints } from "../fixtures";

describe("AtomicConstraints", () => {
    it("should return constraints as string", () => {
        const constraints = AtomicConstraints.fromObjects(atomicConstraints);
        expect(constraints.getAsStringByIndex(0)).to.be.equal("1 1 0");
    });
});
