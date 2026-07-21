import "../setup";

import { LatticeSchema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { expect } from "chai";

import { ReciprocalLattice } from "../../../src/js/lattice/reciprocal/lattice_reciprocal";
import { Na4Cl4, Silicon, SiSlab } from "../fixtures";

const { assertDeepAlmostEqual } = Utils.assertion;

describe("Lattice Reciprocal", () => {
    it("should extract kpoint path", () => {
        const lattice = new ReciprocalLattice(Na4Cl4.lattice as LatticeSchema);
        const expectedPath = [
            {
                point: "Γ",
                steps: 0,
                coordinates: [0, 0, 0],
            },
            {
                point: "R",
                steps: 1,
                coordinates: [0.5, 0.5, 0.5],
            },
        ];
        const actualPath = lattice.extractKpointPath([
            [0, 0, 0],
            [0.5, 0.5, 0.5],
        ]);
        assertDeepAlmostEqual(expectedPath, actualPath);
    });

    it("should return cartesian coordinates of a point", () => {
        const lattice = new ReciprocalLattice(Na4Cl4.lattice as LatticeSchema);
        const expectedCoordinates = [0.5, 0.5, 0.5];
        const actualCoordinates = lattice.getCartesianCoordinates([0.5, 0.5, 0.5]);
        assertDeepAlmostEqual(actualCoordinates, expectedCoordinates);
    });

    it("should return reciprocal vectors", () => {
        const lattice = new ReciprocalLattice(Silicon.lattice as LatticeSchema);
        const actualVectors = lattice.reciprocalVectors;
        const expectedVectors = [
            [1.1547005383792517, -0.40824829046386313, 0],
            [0, 1.2247448713915892, 0],
            [-0.5773502691896261, -0.40824829046386313, 1],
        ];
        assertDeepAlmostEqual(actualVectors, expectedVectors);
    });

    it("should extract symmetry points", () => {
        const lattice = new ReciprocalLattice(Na4Cl4.lattice as LatticeSchema);
        const actualPoints = lattice.symmetryPoints;
        const expectedPoints = [
            {
                point: "Γ",
                coordinates: [0, 0, 0],
            },
            {
                point: "R",
                coordinates: [0.5, 0.5, 0.5],
            },
            {
                point: "X",
                coordinates: [0, 0.5, 0],
            },
            {
                point: "M",
                coordinates: [0.5, 0.5, 0],
            },
        ];
        assertDeepAlmostEqual(actualPoints, expectedPoints);
    });

    it("should calculate k-grid dimensions based on number of points", () => {
        const lattice = new ReciprocalLattice(SiSlab.lattice as LatticeSchema);
        const dimensions = lattice.getDimensionsFromPointsCount(500);
        const expectedDimensions = [12, 12, 4];
        assertDeepAlmostEqual(dimensions, expectedDimensions);
    });

    it("should calculate k-grid dimensions based on spacing in cartesian units", () => {
        const lattice = new ReciprocalLattice(SiSlab.lattice as LatticeSchema);
        const dimensions = lattice.getDimensionsFromSpacing(0.09);
        const expectedDimensions = [12, 12, 4];
        assertDeepAlmostEqual(dimensions, expectedDimensions);
    });

    it("should calculate k-grid dimensions based on spacing in 1/angstrom", () => {
        const lattice = new ReciprocalLattice(SiSlab.lattice as LatticeSchema);
        const dimensions = lattice.getDimensionsFromSpacing(0.11, "angstrom");
        const expectedDimensions = [12, 12, 4];
        assertDeepAlmostEqual(dimensions, expectedDimensions);
    });

    it("should calculate average spacing in 1/angstrom based on k-grid dimensions", () => {
        const lattice = new ReciprocalLattice(SiSlab.lattice as LatticeSchema);
        const dimensions = [12, 12, 4];
        const expectedSpacing = 0.1047;
        const spacing = lattice.getSpacingFromDimensions(dimensions, "angstrom");
        expect(spacing).to.be.almost(expectedSpacing, 1e-4);
    });
});
