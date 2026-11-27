import { Utils } from "@mat3ra/utils";

import { Basis } from "../../../src/js/basis/basis";
import { BasisWithAtomicProperties } from "../../../src/js/basis/basis_with_atomic_properties";
import tools from "../../../src/js/tools";
import {
    H2HFinal,
    H2HImage,
    H2HInitial,
    Si2BasisRepeatedWithLabelAndConstraint,
    Si2BasisWithLabelAndConstraint,
} from "../fixtures";

const { assertDeepAlmostEqual } = Utils.assertion;

describe("Tools:Basis", () => {
    it("should return a repeated basis whose copies keep their atom's label and constraint", () => {
        const basis = new BasisWithAtomicProperties(Si2BasisWithLabelAndConstraint);
        const repeatedBasis = tools.basis.repeat(basis, [2, 1, 1]);
        assertDeepAlmostEqual(Si2BasisRepeatedWithLabelAndConstraint, repeatedBasis.toJSON());
    });

    it("should return interpolated basises", () => {
        const finalBasis = new Basis(H2HFinal.basis);
        const initialBasis = new Basis(H2HInitial.basis);
        const images = tools.basis.interpolate(initialBasis, finalBasis, 1);
        assertDeepAlmostEqual(H2HImage.basis, images[0].toJSON());
    });
});
