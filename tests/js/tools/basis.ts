import { Utils } from "@mat3ra/utils";

import { Basis } from "../../../src/js/basis/basis";
import { BasisWithAtomicProperties } from "../../../src/js/basis/basis_with_atomic_properties";
import tools from "../../../src/js/tools";
import {
    H2HFinal,
    H2HImage,
    H2HInitial,
    Si2BasisRepeatedWithLabelAndConstraint,
    Si2BasisWithIdGap,
    Si2BasisWithIdGapDisplaced,
    Si2BasisWithIdGapHalfway,
    Si2BasisWithLabelAndConstraint,
} from "../fixtures";

const { assertDeepAlmostEqual } = Utils.assertion;

describe("Tools:Basis", () => {
    it("should return a repeated basis whose copies keep their atom's label and constraint", () => {
        const basis = new BasisWithAtomicProperties(Si2BasisWithLabelAndConstraint);
        const repeatedBasis = tools.basis.repeat(basis, [2, 1, 1]);
        assertDeepAlmostEqual(Si2BasisRepeatedWithLabelAndConstraint, repeatedBasis.toJSON());
    });

    [
        { title: "", initial: H2HInitial.basis, final: H2HFinal.basis, image: H2HImage.basis },
        {
            title: " keeping atom ids with gaps",
            initial: Si2BasisWithIdGap,
            final: Si2BasisWithIdGapDisplaced,
            image: Si2BasisWithIdGapHalfway,
        },
    ].forEach(({ title, initial, final, image }) => {
        it(`should return interpolated basises${title}`, () => {
            const images = tools.basis.interpolate(new Basis(initial), new Basis(final), 1);
            assertDeepAlmostEqual(image, images[0].toJSON());
        });
    });
});
