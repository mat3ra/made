import { Coordinate3DSchema, Matrix3X3Schema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { expect } from "chai";

import { Cell } from "../../../src/js/cell/cell";

const { assertDeepAlmostEqual } = Utils.assertion;

const VECTORS: Matrix3X3Schema = [
    [1.0, 0.0, 0.0],
    [0.0, 2.0, 0.0],
    [0.0, 0.0, 3.0],
];

const CELL_JSON = {
    a: VECTORS[0],
    b: VECTORS[1],
    c: VECTORS[2],
    alat: 1,
    units: "angstrom",
};

const POINT_IN_CELL_CRYSTAL: Coordinate3DSchema = [0.5, 0.5, 0.5];
const POINT_OUTSIDE_CELL_CRYSTAL: Coordinate3DSchema = [1.1, 1.1, 1.1];
const POINT_IN_CELL_CARTESIAN: Coordinate3DSchema = [0.5, 1.0, 1.5];

const POINT_IN_CELL: Coordinate3DSchema = [0.5, 0.5, 0.5];
const POINT_OUTSIDE_CELL: Coordinate3DSchema = [1.5, 1.5, 1.5];

// This is in crystal coordinates, but since VECTORS[0] is [1,0,0], it's the same in cartesian
const POINT_IN_CELL_TOLERANCE = 0.01;
const POINT_IN_CELL_WITH_TOLERANCE_0_1: Coordinate3DSchema = [0.99, 0.5, 0.5];
const POINT_OUTSIDE_CELL_WITH_TOLERANCE_0_1: Coordinate3DSchema = [1.01, 0.5, 0.5];
const POINT_OUTSIDE_CELL_WITH_TOLERANCE_0_1_ALT: Coordinate3DSchema = [0.999, 0.5, 0.5];

const VECTORS_VOLUME = 6.0;

const VECTORS_EQUAL_UP_TO_PRECISION_4: Matrix3X3Schema = [
    [1.00001, 0.0, 0.0],
    [0.0, 2.00001, 0.0],
    [0.0, 0.0, 3.00001],
];

const VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME = 6.000110000600001;
const VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME_ROUNDED_TO_PRECISION_4 = 6.0001;
const VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME_ROUNDED_TO_PRECISION_5 = 6.00011;

const SCALING_MATRIX: Matrix3X3Schema = [
    [2, 0, 0],
    [0, 2, 0],
    [0, 0, 2],
];

const VECTORS_SCALED_BY_MATRIX = [
    [2.0, 0.0, 0.0],
    [0.0, 4.0, 0.0],
    [0.0, 0.0, 6.0],
];

describe("Cell", () => {
    it("cell creation", () => {
        const cell = new Cell({
            a: VECTORS[0],
            b: VECTORS[1],
            c: VECTORS[2],
        });
        expect(cell.a).to.deep.equal(VECTORS[0]);
        expect(cell.b).to.deep.equal(VECTORS[1]);
        expect(cell.c).to.deep.equal(VECTORS[2]);
    });
    it("cell creation default", () => {
        const cell = new Cell();
        expect(cell.a).to.deep.equal(Cell.defaultConfig.a);
        expect(cell.b).to.deep.equal(Cell.defaultConfig.b);
        expect(cell.c).to.deep.equal(Cell.defaultConfig.c);
    });
    it("from vectors array", () => {
        const cell = Cell.fromVectorsArray(VECTORS);
        expect(cell.a).to.deep.equal(VECTORS[0]);
        expect(cell.b).to.deep.equal(VECTORS[1]);
        expect(cell.c).to.deep.equal(VECTORS[2]);
    });
    it("get vector arrays", () => {
        const cell = new Cell({
            a: VECTORS[0],
            b: VECTORS[1],
            c: VECTORS[2],
        });
        expect(cell.vectorArrays).to.deep.equal(VECTORS);
    });
    it("vector arrays including rounded", () => {
        const classReference = Cell;
        classReference.RoundedVector3DClassReference.roundPrecision = 4;
        const cell = classReference.fromVectorsArray(VECTORS_EQUAL_UP_TO_PRECISION_4);
        expect(cell.vectorArrays).to.deep.equal(VECTORS_EQUAL_UP_TO_PRECISION_4);
        expect(cell.vectorArraysRounded).to.deep.equal(VECTORS);

        classReference.RoundedVector3DClassReference.roundPrecision = 5;
        const cellRounded = classReference.fromVectorsArray(VECTORS_EQUAL_UP_TO_PRECISION_4);
        expect(cellRounded.vectorArrays).to.deep.equal(VECTORS_EQUAL_UP_TO_PRECISION_4);
        expect(cellRounded.vectorArraysRounded).not.to.deep.equal(VECTORS);
    });
    it("convert point to cartesian", () => {
        const cell = Cell.fromVectorsArray(VECTORS);
        const cartesian = cell.convertPointToCartesian(POINT_IN_CELL_CRYSTAL);
        expect(cartesian).to.deep.equal(POINT_IN_CELL_CARTESIAN);
    });
    it("convert point to crystal", () => {
        const cell = Cell.fromVectorsArray(VECTORS);
        const point = cell.convertPointToCrystal(POINT_IN_CELL_CARTESIAN);
        expect(point).to.deep.equal(POINT_IN_CELL_CRYSTAL);
    });
    it("volume", () => {
        const cell = Cell.fromVectorsArray(VECTORS);
        const { volume } = cell;
        expect(volume).to.equal(VECTORS_VOLUME);
    });
    it("volume rounded", () => {
        const classReference = Cell;
        classReference.roundPrecision = 4;
        const cell = classReference.fromVectorsArray(VECTORS_EQUAL_UP_TO_PRECISION_4);
        const { volume, volumeRounded } = cell;
        expect(volume).to.equal(VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME);
        expect(volumeRounded).to.equal(
            VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME_ROUNDED_TO_PRECISION_4,
        );

        classReference.roundPrecision = 5;
        const cellRounded1 = classReference.fromVectorsArray(VECTORS_EQUAL_UP_TO_PRECISION_4);
        expect(cellRounded1.volume).to.equal(VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME);
        expect(cellRounded1.volumeRounded).to.equal(
            VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME_ROUNDED_TO_PRECISION_5,
        );
        expect(cellRounded1.volumeRounded).not.to.equal(
            VECTORS_EQUAL_UP_TO_PRECISION_4_VOLUME_ROUNDED_TO_PRECISION_4,
        );
    });

    // Unique to JS/TS

    it("clone", () => {
        const cell = Cell.fromVectorsArray(VECTORS);
        const clonedCell = cell.clone();
        expect(clonedCell).not.to.equal(cell);
        expect(clonedCell).to.deep.equal(cell);
    });
    it("clone and scale by matrix", () => {
        const cell = Cell.fromVectorsArray(VECTORS);
        const clonedCell = cell.cloneAndScaleByMatrix(SCALING_MATRIX);
        expect(clonedCell).not.to.equal(cell);
        assertDeepAlmostEqual(clonedCell.vectorArrays, VECTORS_SCALED_BY_MATRIX);
    });
    it("scale by matrix", () => {
        const cell = Cell.fromVectorsArray(VECTORS);
        cell.scaleByMatrix(SCALING_MATRIX);
        assertDeepAlmostEqual(cell.vectorArrays, VECTORS_SCALED_BY_MATRIX);
    });
    it("is point inside cell", () => {
        const cell = Cell.fromVectorsArray(VECTORS);
        expect(cell.isPointInsideCell(POINT_IN_CELL)).to.equal(true);
        expect(cell.isPointInsideCell(POINT_OUTSIDE_CELL)).to.equal(false);
    });
    it("is point inside cell with tolerance", () => {
        const classReference = Cell;
        classReference.tolerance = POINT_IN_CELL_TOLERANCE;
        const cell = Cell.fromVectorsArray(VECTORS);
        expect(cell.isPointInsideCell(POINT_IN_CELL_WITH_TOLERANCE_0_1)).to.equal(true);
        expect(cell.isPointInsideCell(POINT_OUTSIDE_CELL_WITH_TOLERANCE_0_1)).to.equal(false);
        expect(cell.isPointInsideCell(POINT_OUTSIDE_CELL_WITH_TOLERANCE_0_1_ALT)).to.equal(false);
    });
    it("is point inside cell crystal", () => {
        const cell = Cell.fromVectorsArray(VECTORS);
        const pointInCellCrystal = cell.convertPointToCrystal(POINT_IN_CELL_CARTESIAN);
        expect(cell.isPointInsideCellCrystal(pointInCellCrystal)).to.equal(true);
        expect(cell.isPointInsideCellCrystal(POINT_OUTSIDE_CELL_CRYSTAL)).to.equal(false);
    });
    it("toJSON", () => {
        const cell = Cell.fromVectorsArray(VECTORS);
        const json = cell.toJSON();
        expect(json).to.deep.equal(CELL_JSON);
    });
});
