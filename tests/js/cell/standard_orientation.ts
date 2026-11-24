import { LatticeSchema, LatticeTypeEnum, Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { expect } from "chai";

import { getPrimitiveLatticeVectorsFromConfig } from "../../../src/js/cell/primitive_cell";
import { Lattice } from "../../../src/js/lattice/lattice";

const TOLERANCE = 1e-6;

// Conventional parameters per type, generic enough to have no accidental extra symmetry.
const CONVENTIONAL_PARAMETERS: Record<string, Partial<LatticeSchema>> = {
    CUB: { a: 3.0 },
    FCC: { a: 4.0 },
    BCC: { a: 3.2 },
    TET: { a: 3.0, c: 4.1 },
    BCT: { a: 3.0, c: 4.1 },
    ORC: { a: 3.0, b: 3.6, c: 4.3 },
    ORCF: { a: 3.0, b: 3.6, c: 4.3 },
    ORCI: { a: 3.0, b: 3.6, c: 4.3 },
    ORCC: { a: 3.0, b: 3.6, c: 4.3 },
    HEX: { a: 3.0, c: 4.8 },
    RHL: { a: 3.5, alpha: 70.0, beta: 70.0, gamma: 70.0 },
    MCL: { a: 3.0, b: 3.6, c: 4.3, alpha: 75.0 },
    MCLC: { a: 3.0, b: 3.6, c: 4.3, alpha: 75.0 },
    TRI: { a: 3.0, b: 3.6, c: 4.3, alpha: 75.0, beta: 80.0, gamma: 85.0 },
};

function standardCell(type: string): Matrix3X3Schema {
    const parameters = { alpha: 90, beta: 90, gamma: 90, ...CONVENTIONAL_PARAMETERS[type] };
    const a = parameters.a as number;
    return getPrimitiveLatticeVectorsFromConfig({
        b: a,
        c: a,
        ...parameters,
        type: type as LatticeTypeEnum,
    } as LatticeSchema);
}

/**
 * A lattice as a stored material holds it: parameters and type, no vectors.
 */
function latticeFromParameters(type: string): Lattice {
    const shape = Lattice.fromVectorsArray(standardCell(type), undefined, type as LatticeTypeEnum);
    const { a, b, c, alpha, beta, gamma } = shape;
    return new Lattice({ a, b, c, alpha, beta, gamma, type } as LatticeSchema);
}

function expectClose(actual: number[][], expected: number[][]) {
    actual.forEach((row, i) =>
        row.forEach((value, j) => expect(value).to.be.closeTo(expected[i][j], TOLERANCE)),
    );
}

function metric(vectors: Matrix3X3Schema): number[][] {
    return Utils.math.multiply(vectors, Utils.math.transpose(vectors)) as unknown as number[][];
}

describe("Lattice vectors in standard orientation", () => {
    Object.keys(CONVENTIONAL_PARAMETERS).forEach((type) => {
        it(`are the standard primitive cell of ${type}`, () => {
            const lattice = latticeFromParameters(type);
            expectClose(lattice.vectorArraysInStandardOrientation, standardCell(type));
        });

        it(`are a rotation of the generic ${type} vectors`, () => {
            const lattice = latticeFromParameters(type);
            const generic = lattice.vectorArrays;
            const standard = lattice.vectorArraysInStandardOrientation;
            expectClose(metric(standard), metric(generic));
            expect(Utils.math.det(standard) as number).to.be.closeTo(
                Utils.math.det(generic) as number,
                TOLERANCE,
            );
        });
    });

    it("keep the vectors of a lattice not shaped like its type", () => {
        const lattice = new Lattice({
            a: 2.6,
            b: 2.6,
            c: 2.6,
            alpha: 70,
            beta: 70,
            gamma: 70,
            type: "FCC",
        } as LatticeSchema);
        expectClose(lattice.vectorArraysInStandardOrientation, lattice.vectorArrays);
    });

    it("leave the generic vectors as they are", () => {
        const [vectorA, , vectorC] = latticeFromParameters("FCC").vectorArrays;
        expect(vectorA[1]).to.equal(0);
        expect(vectorC[0]).to.equal(0);
        expect(vectorC[1]).to.equal(0);
    });
});
