import "../setup";

import { LatticeSchema } from "@mat3ra/esse/dist/js/types";
import { expect } from "chai";

import { computeBrillouinZone } from "../../../src/js/lattice/reciprocal/brillouin_zone";
import { ReciprocalLattice } from "../../../src/js/lattice/reciprocal/lattice_reciprocal";
import { Graphene, Na4Cl4, Silicon, SiSlab } from "../fixtures";

/** Distinct vertices across all faces, keyed by rounded coordinates. */
function countVertices(faces: NonNullable<ReturnType<typeof computeBrillouinZone>>): number {
    const keys = new Set<string>();
    faces.forEach((face) =>
        face.vertices.forEach((vertex) =>
            keys.add(vertex.map((component) => component.toFixed(5)).join(",")),
        ),
    );
    return keys.size;
}

function countEdges(faces: NonNullable<ReturnType<typeof computeBrillouinZone>>): number {
    return faces.reduce((sum, face) => sum + face.vertices.length, 0) / 2;
}

function extentAlongThirdAxis(faces: NonNullable<ReturnType<typeof computeBrillouinZone>>): number {
    const coordinates = faces.flatMap((face) => face.vertices.map((vertex) => vertex[2]));
    return Math.max(...coordinates) - Math.min(...coordinates);
}

describe("Brillouin Zone", () => {
    it("should be a truncated octahedron for a face-centered cubic lattice", () => {
        const faces = new ReciprocalLattice(Silicon.lattice as LatticeSchema).brillouinZone;
        expect(faces).to.not.be.null;
        // 8 hexagons on the <111> planes and 6 squares on the <200> planes.
        expect(faces).to.have.lengthOf(14);
        expect(faces!.filter((face) => face.vertices.length === 6)).to.have.lengthOf(8);
        expect(faces!.filter((face) => face.vertices.length === 4)).to.have.lengthOf(6);
        expect(countVertices(faces!)).to.be.equal(24);
    });

    it("should be a cube for a simple cubic lattice", () => {
        const faces = new ReciprocalLattice(Na4Cl4.lattice as LatticeSchema).brillouinZone;
        expect(faces).to.not.be.null;
        expect(faces).to.have.lengthOf(6);
        expect(countVertices(faces!)).to.be.equal(8);
        faces!.forEach((face) => expect(face.vertices).to.have.lengthOf(4));
    });

    it("should be a hexagonal prism for a hexagonal lattice", () => {
        const faces = new ReciprocalLattice(Graphene.lattice as LatticeSchema).brillouinZone;
        expect(faces).to.not.be.null;
        expect(faces).to.have.lengthOf(8);
        expect(faces!.filter((face) => face.vertices.length === 6)).to.have.lengthOf(2);
        expect(faces!.filter((face) => face.vertices.length === 4)).to.have.lengthOf(6);
    });

    it("should follow the lattice itself, not only its type", () => {
        // A slab pads the cell with vacuum along the third axis, which shrinks the
        // corresponding reciprocal vector and flattens the zone.
        const bulk = new ReciprocalLattice(Silicon.lattice as LatticeSchema).brillouinZone;
        const slab = new ReciprocalLattice(SiSlab.lattice as LatticeSchema).brillouinZone;
        expect(bulk).to.not.be.null;
        expect(slab).to.not.be.null;
        expect(extentAlongThirdAxis(slab!)).to.be.lessThan(extentAlongThirdAxis(bulk!));
    });

    it("should be a closed convex polyhedron", () => {
        [Silicon, Na4Cl4, Graphene, SiSlab].forEach((material) => {
            const faces = new ReciprocalLattice(material.lattice as LatticeSchema).brillouinZone;
            expect(faces).to.not.be.null;
            // Euler characteristic of a convex polyhedron: V - E + F = 2.
            expect(countVertices(faces!) - countEdges(faces!) + faces!.length).to.be.equal(2);
        });
    });

    it("should enclose the origin and no other reciprocal lattice point", () => {
        const lattice = new ReciprocalLattice(Silicon.lattice as LatticeSchema);
        const faces = lattice.brillouinZone!;
        const [firstVector] = lattice.reciprocalVectors;
        faces.forEach((face) => {
            face.vertices.forEach((vertex) => {
                const distanceToOrigin = Math.hypot(...vertex);
                const distanceToNeighbour = Math.hypot(
                    vertex[0] - firstVector[0],
                    vertex[1] - firstVector[1],
                    vertex[2] - firstVector[2],
                );
                expect(distanceToOrigin).to.be.at.most(distanceToNeighbour + 1e-6);
            });
        });
    });

    it("should return null for degenerate reciprocal vectors", () => {
        expect(
            computeBrillouinZone([
                [1, 0, 0],
                [1, 0, 0],
                [0, 0, 1],
            ]),
        ).to.be.equal(null);
        expect(computeBrillouinZone([[1, 0, 0]])).to.be.equal(null);
    });
});
