import "../setup";

import { Vector3DSchema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { expect } from "chai";

import { Basis } from "../../../src/js/basis/basis";
import { ConstrainedBasis } from "../../../src/js/basis/constrained_basis";
import Material from "../../../src/js/Material";
import {
    AsGeBasis,
    C2H4,
    C2H4Translated,
    FeLiSiBasis,
    FeOStandata,
    LiFeSiBasis,
    LiFeSiBasisLabels,
    Na,
    Na4Cl4,
    Na4Cl4Cartesian,
} from "../fixtures";

const { assertDeepAlmostEqual } = Utils.assertion;
const TOLERANCE = 1e-4;

const FeOAntiferromagnetic = {
    ...FeOStandata,
    basis: {
        ...FeOStandata.basis,
        labels: [
            { id: 0, value: 1 },
            { id: 1, value: 2 },
        ],
        startingMagnetization: [
            { id: 0, value: 0.5 },
            { id: 1, value: -0.5 },
        ],
    },
};

const FeOAntiferromagneticWithIdGap = {
    ...FeOAntiferromagnetic,
    basis: {
        ...FeOAntiferromagnetic.basis,
        elements: FeOAntiferromagnetic.basis.elements.slice(1),
        coordinates: FeOAntiferromagnetic.basis.coordinates.slice(1),
    },
};

describe("Basis", () => {
    it("should return true if basises are equal", () => {
        const basis1 = new Basis(FeLiSiBasis);
        const basis2 = new Basis(LiFeSiBasis);
        expect(basis1.isEqualTo(basis2)).to.be.equal(true);
    });

    it("should return true when basis is compared to its clone", () => {
        const basis1 = new Material(Na4Cl4).getBasis();
        const basis2 = basis1.clone();
        expect(basis1.isEqualTo(basis2)).to.be.equal(true);
        expect(basis1.hasEquivalentCellTo(basis2)).to.be.equal(true);
    });

    it("should return jsonified basis", () => {
        const basis = new Material(Na4Cl4).getBasis();
        expect(basis.toJSON()).to.be.deep.almost.equal(Na4Cl4.basis);
    });

    it("should return true if cells are equal", () => {
        const basis1 = new Material(Na4Cl4).getBasis();
        const basis2 = new Material(Na4Cl4Cartesian).getBasis();
        expect(basis1.hasEquivalentCellTo(basis2)).to.be.equal(true);
    });

    /**
     * Elements
     */

    it("should return Na4Cl4 as unitCellFormula", () => {
        const basis = new Basis(Na4Cl4.basis);
        expect(basis.unitCellFormula).to.be.equal("Na4Cl4");
    });

    it("should return NaCl as formula", () => {
        const basis = new Basis(Na4Cl4.basis);
        expect(basis.formula).to.be.equal("NaCl");
    });

    it("should return elements", () => {
        const basis = new Basis(Na4Cl4.basis);
        expect(basis.elements).to.be.deep.almost.equal(Na4Cl4.basis.elements);
    });

    it("should return unique elements", () => {
        const basis = new Basis(Na4Cl4.basis);
        expect(basis.uniqueElements).to.be.deep.equal(["Na", "Cl"]);
    });

    it("should return elements count", () => {
        const basis = new Basis(Na4Cl4.basis);
        expect(basis.elementCounts).to.be.deep.equal([
            {
                value: "Na",
                count: 4,
            },
            {
                value: "Cl",
                count: 4,
            },
        ]);
    });

    it("should set elements", () => {
        const basis = new Basis(Na4Cl4.basis);
        basis.elements = AsGeBasis.elements;
        expect(basis.elements).to.be.deep.equal(AsGeBasis.elements);
    });

    /**
     * Coordinates
     */

    it("should return coordinates", () => {
        const basis = new Basis(Na4Cl4.basis);
        expect(basis.coordinates).to.be.deep.almost.equal(Na4Cl4.basis.coordinates);
    });

    it("should set coordinates", () => {
        const basis = new Basis(Na4Cl4.basis);
        basis.coordinates = AsGeBasis.coordinates;
        expect(basis.coordinates).to.be.deep.almost.equal(AsGeBasis.coordinates);
    });

    it("should return coordinate by id", () => {
        const basis = new Basis(Na4Cl4.basis);
        expect(basis.getCoordinateValueById(3)).to.be.deep.equal([0.5, 0.5, 0]);
    });

    /**
     * Units
     */

    it("should return true if basis is in crystal units", () => {
        const basis = new Basis(Na4Cl4.basis);
        expect(basis.isInCrystalUnits).to.be.equal(true);
    });

    it("should convert crystal to cartesian", () => {
        const basis = new Material(Na4Cl4).getBasis();
        basis.toCartesian();
        expect(basis.isInCartesianUnits).to.be.equal(true);
        expect(basis.coordinates).to.be.deep.almost.equal(Na4Cl4Cartesian.basis.coordinates);
    });

    /**
     * Labels
     */

    it("should return elements with labels", () => {
        const basis = new ConstrainedBasis({ ...LiFeSiBasisLabels, constraints: [] });
        const elementsWithLabels = basis.elementsWithLabelsArray;
        const expectedElementsWithLabels = ["Li0", "Fe1", "Si2"];
        expect(elementsWithLabels).to.be.deep.equal(expectedElementsWithLabels);
    });

    it("should return labels and starting magnetization by atom id", () => {
        const basis = new ConstrainedBasis({
            elements: [
                { id: 0, value: "Fe" },
                { id: 2, value: "Fe" },
            ],
            coordinates: [
                { id: 0, value: [0, 0, 0] },
                { id: 2, value: [0.5, 0.5, 0.5] },
            ],
            constraints: [],
            labels: [
                { id: 2, value: 1 },
                { id: 0, value: 0 },
            ],
            startingMagnetization: [{ id: 2, value: -0.5 }],
        });
        const clone = basis.clone();
        expect(clone.atomicLabelsArray).to.be.deep.equal([0, 1]);
        expect(clone.startingMagnetizationArray).to.be.deep.equal([0, -0.5]);
        basis.removeAllAtoms();
        const { labels, startingMagnetization } = basis.clone();
        expect([labels, startingMagnetization]).to.be.deep.equal([[], []]);
    });

    it("should keep cleared labels and starting magnetization cleared through setBasis", () => {
        const material = new Material(FeOAntiferromagnetic);
        const basis = material.getBasis();
        basis.labels = [];
        basis.startingMagnetization = [];
        material.setBasis(basis.toJSON());
        const { labels, startingMagnetization } = material.getBasis();
        expect([labels, startingMagnetization]).to.be.deep.equal([[], []]);
    });

    /**
     * Species
     */

    it("should name one species per element and starting magnetization", () => {
        const basis = new Material(FeOAntiferromagnetic).getBasis();
        expect(basis.atomicSpeciesArray).to.be.deep.equal(["Fe", "Fe1", "O", "O"]);
        expect(basis.uniqueAtomicSpecies).to.be.deep.equal([
            { name: "Fe", element: "Fe", startingMagnetization: 0.5 },
            { name: "Fe1", element: "Fe", startingMagnetization: -0.5 },
            { name: "O", element: "O", startingMagnetization: 0 },
        ]);
    });

    it("should refuse more starting magnetization values per element than species names fit", () => {
        const values = Array.from({ length: 11 }, (_, index) => index / 10);
        const basis = ConstrainedBasis.fromElementsCoordinatesAndConstraints({
            elements: values.map(() => "Fe"),
            coordinates: values.map((value) => [value, 0, 0]),
            constraints: values.map(() => [true, true, true]),
        });
        basis.startingMagnetization = values.map((value, id) => ({ id, value }));
        expect(() => basis.atomicSpeciesArray).to.throw(
            "Fe has more than 10 distinct starting magnetization values",
        );
    });

    it("should print species, not labels, in atomic positions", () => {
        const basis = new Material(FeOAntiferromagnetic).getBasis();
        const species = ["Fe", "Fe1", "O", "O"];
        const firstWords = (lines: string[]) => lines.map((line) => line.split(" ")[0]);
        expect(firstWords(basis.atomicPositions)).to.be.deep.equal(species);
        expect(basis.elementsCoordinatesConstraintsArray.map(([, name]) => name)).to.be.deep.equal(
            species,
        );
        expect(firstWords(basis.getAtomicPositionsWithConstraintsAsStrings())).to.be.deep.equal(
            species,
        );
    });

    it("should print labels, not species, in XYZ", () => {
        const xyz = new Material(FeOAntiferromagnetic).getBasisAsXyz();
        expect(xyz.match(/^\S+/gm)).to.be.deep.equal(["Fe1", "Fe2", "O", "O"]);
    });

    it("should print the given atom names in XYZ", () => {
        const material = new Material(FeOAntiferromagnetic);
        const elements = material.getBasis().elements.map(({ value }) => value);
        const xyz = material.getBasisAsXyz(false, elements);
        expect(xyz.match(/^\S+/gm)).to.be.deep.equal(["Fe", "Fe", "O", "O"]);
    });

    [
        {
            edit: "an appended atom",
            config: FeOAntiferromagnetic,
            editLines: (lines: string[]) => [...lines, lines[3]],
            expectedLabels: FeOAntiferromagnetic.basis.labels,
            expectedStartingMagnetization: FeOAntiferromagnetic.basis.startingMagnetization,
        },
        {
            edit: "removed atoms",
            config: FeOAntiferromagnetic,
            editLines: (lines: string[]) => lines.slice(0, 1),
            expectedLabels: [{ id: 0, value: 1 }],
            expectedStartingMagnetization: [{ id: 0, value: 0.5 }],
        },
        {
            edit: "an id gap",
            config: FeOAntiferromagneticWithIdGap,
            editLines: (lines: string[]) => lines,
            expectedLabels: [{ id: 0, value: 2 }],
            expectedStartingMagnetization: [{ id: 0, value: -0.5 }],
        },
        {
            edit: "a pasted labelled export",
            config: FeOStandata,
            editLines: () => new Material(FeOAntiferromagnetic).getBasisAsXyz().trim().split("\n"),
            expectedLabels: FeOAntiferromagnetic.basis.labels,
            expectedStartingMagnetization: [],
        },
        {
            edit: "a typed label",
            config: FeOAntiferromagnetic,
            editLines: (lines: string[]) => [lines[0].replace("Fe", "Fe2"), ...lines.slice(1)],
            expectedLabels: [
                { id: 0, value: 2 },
                { id: 1, value: 2 },
            ],
            expectedStartingMagnetization: FeOAntiferromagnetic.basis.startingMagnetization,
        },
        {
            edit: "its own labelled export pasted back",
            config: FeOAntiferromagnetic,
            editLines: () => new Material(FeOAntiferromagnetic).getBasisAsXyz().trim().split("\n"),
            expectedLabels: FeOAntiferromagnetic.basis.labels,
            expectedStartingMagnetization: FeOAntiferromagnetic.basis.startingMagnetization,
        },
    ].forEach(({ edit, config, editLines, expectedLabels, expectedStartingMagnetization }) => {
        it(`should copy labels and starting magnetization by index after XYZ text with ${edit}`, () => {
            const material = new Material(config);
            const elements = material.getBasis().elements.map(({ value }) => value);
            const lines = material.getBasisAsXyz(false, elements).trim().split("\n");
            const editedMaterial = material.clone();
            editedMaterial.setBasis(editLines(lines).join("\n"), "xyz", material.basis.units);
            const basis = editedMaterial.getBasis();
            basis.copyLabelsAndStartingMagnetizationByIndex(material.getBasis());
            expect([basis.labels, basis.startingMagnetization]).to.be.deep.equal([
                expectedLabels,
                expectedStartingMagnetization,
            ]);
        });
    });

    /**
     * Atoms
     */

    it("should add a new atom", () => {
        const basis = new Basis(Na4Cl4.basis);
        basis.addAtom({
            element: "Ge",
            coordinate: [0, 0.25, 0.25],
        });
        expect(basis.elements).to.be.deep.equal([
            ...Na4Cl4.basis.elements,
            {
                id: 8,
                value: "Ge",
            },
        ]);
        expect(basis.coordinates).to.be.deep.almost.equal([
            ...Na4Cl4.basis.coordinates,
            {
                id: 8,
                value: [0, 0.25, 0.25],
            },
        ]);
    });

    it("should remove an atom", () => {
        const basis = new Basis(Na4Cl4.basis);
        basis.removeAtom({
            id: 3,
            element: "Na",
            coordinate: [0.5, 0.5, 0],
        });
        expect(basis.elements.length).to.be.equal(7);
        expect(basis.coordinates.length).to.be.equal(7);
    });

    it("should return number of atoms", () => {
        const basis = new Basis(Na4Cl4.basis);
        expect(basis.nAtoms).to.be.equal(8);
    });

    /**
     * Hash
     */

    it("should return the string", () => {
        const basis = new Basis(Na4Cl4.basis);
        const string =
            "Cl 0,0,0.5;Cl 0,0.5,0;Cl 0.5,0,0;Cl 0.5,0.5,0.5;Na 0,0,0;Na 0,0.5,0.5;Na 0.5,0,0.5;Na 0.5,0.5,0;";
        expect(basis.getAsSortedString()).to.be.equal(string);
    });

    /**
     * Representation
     */

    it("should return standard representation", () => {
        const basis = new Material(Na4Cl4Cartesian).getBasis();
        assertDeepAlmostEqual(basis.standardRepresentation, Na4Cl4.basis, ["constraints"]);
    });

    /**
     * Minimum lattice size generated for a molecule with more than one atom.
     * The minimumLatticeSize is the maximum pairwise distance between two atoms
     * of the structure, C2H4 in this case.
     */
    it("should return minimum lattice size for a molecule", () => {
        const basis = new Basis(C2H4.basis);
        const minimumLatticeSize = 3.1622776601683795;
        const latticeSize = basis.getMinimumLatticeSize();
        expect(latticeSize).to.be.almost(minimumLatticeSize, TOLERANCE);
    });

    /**
     * Minimum lattice size generated for a structure made up of a single atom.
     * The minimumLatticeSize is the atomic radii of the atom, Na in this case, in units of angstroms.
     */
    it("should return minimum lattice size for an atom", () => {
        const basis = new Basis(Na.basis);
        const minimumLatticeSize = 3;
        const latticeSize = basis.getMinimumLatticeSize();
        expect(latticeSize).to.be.equal(minimumLatticeSize);
    });

    //* * Pairwise Distance */
    it("should return max distance", () => {
        const basis = new Basis(C2H4.basis);
        const maxDistance = 1.5811388300841898;
        expect(basis.maxPairwiseDistance).to.be.almost(maxDistance, TOLERANCE);
    });

    //* * Center of Coordinates */
    it("should return center of coordinates", () => {
        const basis = new Basis(C2H4.basis);
        const centerOfCoordinatesArray = [0.3333, -0.0417, 0.0917];
        const basisCenterOfCoordinatesPoint = basis.centerOfCoordinatesPoint;
        assertDeepAlmostEqual(basisCenterOfCoordinatesPoint, centerOfCoordinatesArray);
    });

    //* * Translation by Vector */
    it("should return the updated basis coordinates", () => {
        const basis = new Basis(C2H4.basis);
        const translationVector = [1.6917, 1.9667, 2] as Vector3DSchema;
        basis.translateByVector(translationVector);
        assertDeepAlmostEqual(basis.coordinates, C2H4Translated.basis.coordinates);
    });
});
