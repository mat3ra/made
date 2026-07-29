import { AtomicConstraintsSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";
import { isEmpty, isNaN, map } from "lodash";
import s from "underscore.string";

import { ConstrainedBasis, ConstrainedBasisConfig } from "../basis/constrained_basis";
import { AtomicCoordinateValue } from "../basis/coordinates";
import { AtomicElementValue } from "../basis/elements";
import { Cell } from "../cell/cell";
import { AtomicConstraintValue } from "../constraints/constraints";
import { Lattice } from "../lattice/lattice";
import { InvalidLineError } from "./errors";
import { CombinatorialBasis } from "./xyz_combinatorial_basis";

// Regular expression for an XYZ line with atomic constraints, eg. Si    0.000000    0.500000    0.446678 1 1 1`
// eslint-disable-next-line max-len
const XYZ_LINE_REGEX =
    /[A-Z][a-z]?(\d)?\s+((-?\d+\.?\d*|\.\d+)\s+(-?\d+\.?\d*|\.\d+)\s+(-?\d+\.?\d*|\.\d+)(\s+)?(\s+[0-1]\s+[0-1]\s+[0-1](\s+)?)?)$/;

export const XYZ_COORDINATE_PRECISION = 4;
/**
 * Validates XYZ file's line. Line should be in following format "Si 0.5 0.5 0.5".
 * Raises an error if line is in wrong format.
 */
function validateLine(xyzLine: string, index: number) {
    const words = xyzLine.split(" ").filter((x) => x.trim() !== "");

    if (!xyzLine.match(XYZ_LINE_REGEX)) {
        throw new InvalidLineError(index, xyzLine);
    }

    const coordinates = [parseFloat(words[1]), parseFloat(words[2]), parseFloat(words[3])];
    coordinates.forEach((num, i) => {
        if (isNaN(num)) {
            throw new Error(`Coordinates should be a number. Possible error in ${i} coordinate`);
        }
    });
}

/**
 * Validates that passed string is well-formed XYZ file.
 */
export function validate(xyzTxt: string) {
    // The @types/underscore.string package does not provide interfaces for function chaining at the moment. Disable TS here
    // @ts-ignore
    s(xyzTxt)
        .trim()
        .lines()
        .filter((x: string) => x.trim() !== "")
        .forEach(validateLine);
}

export interface ParsedObject {
    element: AtomicElementValue;
    coordinate: AtomicCoordinateValue;
    constraints: AtomicConstraintValue;
    label?: number;
}

/**
 * Parses XYZ line and returns an object.
 * @param line - line of text
 */
function _parseXYZLineAsWords(line: string): ParsedObject {
    const words = s.words(line);
    const elementWithOptionalLabel = words[0];
    const element = elementWithOptionalLabel.replace(/\d$/, "") as AtomicElementValue; // Fe1 => Fe
    const generateConstraintValue = (n: number) => parseInt(`${n}`, 10) !== 0;

    const basisLineConfig: ParsedObject = {
        element,
        coordinate: [+words[1], +words[2], +words[3]],
        // Below maps zero values to false (atom is fixed) and non-zero values to true (atom is moving)
        constraints: [
            generateConstraintValue(+words[4]),
            generateConstraintValue(+words[5]),
            generateConstraintValue(+words[6]),
        ],
    };

    if (elementWithOptionalLabel !== element) {
        return {
            ...basisLineConfig,
            label: parseInt(elementWithOptionalLabel[elementWithOptionalLabel.length - 1], 10),
        };
    }

    return basisLineConfig;
}

/**
 * Parse XYZ text for basis.
 * @param txt Text
 * @param units Coordinate units
 * @param cell Basis Cell
 */
function toBasisConfig(txt: string, units = "angstrom", cell = new Cell()): ConstrainedBasisConfig {
    // @ts-ignore
    const lines: string[] = s(txt).trim().lines();
    const listOfObjects = map(lines, _parseXYZLineAsWords);

    const basisConfig = {
        elements: listOfObjects.map((elm, idx) => {
            return {
                id: idx,
                value: elm.element,
            };
        }),
        coordinates: listOfObjects.map((elm, idx) => {
            return {
                id: idx,
                value: elm.coordinate,
            };
        }),
        units,
        cell,
        constraints: listOfObjects.map((elm, idx) => {
            return {
                id: idx,
                value: elm.constraints,
            };
        }),
    };

    const labels: {
        id: number;
        value: number;
    }[] = [];

    listOfObjects.forEach((elm, idx) => {
        if (elm.label) {
            labels.push({
                id: idx,
                value: elm.label,
            });
        }
    });

    if (!isEmpty(labels)) {
        return {
            ...basisConfig,
            labels,
        } as ConstrainedBasisConfig;
    }

    return basisConfig as ConstrainedBasisConfig;
}

/**
 * Create XYZ from Basis class instance.
 * @param basisClsInstance Basis class instance.
 * @param coordinatePrintFormat Output format for coordinates.
 * @return Basis string in XYZ format
 */
function fromBasis(basisClsInstance: ConstrainedBasis, coordinatePrintFormat: string): string {
    const XYZArray = basisClsInstance.getAtomicPositionsWithConstraintsAsStrings(
        coordinatePrintFormat,
        XYZ_COORDINATE_PRECISION,
    );
    return `${XYZArray.join("\n")}\n`;
}

/**
 * Create XYZ from Material class instance (or its JSON config).
 * Constraints are not part of ESSE basis — pass them separately.
 * Prefer fromBasis when you already have a ConstrainedBasis instance.
 */
function fromMaterial(
    materialOrConfig: MaterialSchema,
    fractional = false,
    constraints: AtomicConstraintsSchema = [],
): string {
    const lattice = new Lattice(materialOrConfig.lattice);
    const basis = new ConstrainedBasis({
        ...materialOrConfig.basis,
        cell: Cell.fromVectorsArray(lattice.vectorArrays),
        constraints,
    });
    if (fractional) {
        basis.toCrystal();
    }
    return fromBasis(basis, "%11.6f");
}

export default {
    validate,
    fromMaterial,
    toBasisConfig,
    fromBasis,
    CombinatorialBasis,
};
