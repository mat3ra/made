"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.CombinatorialBasis = exports.WrongBasisFormat = void 0;
const math_1 = require("@mat3ra/code/dist/js/math");
const lodash_1 = require("lodash");
const s = __importStar(require("underscore.string"));
const cell_1 = require("../cell/cell");
/**
 * @summary Combinatorial XYZ basis class and related. Create and get all information about basis and elements in it.
 * Constructor accepts string in extended XYZ format. Extended XYZ format is as follows:
 *
 * 1. Regular XYZ
 * ```
 *      Si 0.0 0.0 0.0
 *      Li 0.5 0.5 0.5
 * ```
 * 2. Permutation (slash-separated)
 * ```
 *      Si/Ge/As 0.0 0.0 0.0
 *      Si/Ge    0.5 0.5 0.0
 * ```
 * 3. Combination (comma-separated)
 * ```
 *      Si,Ge,As 0.0 0.0 0.0
 *      Si,Ge    0.5 0.5 0.0
 * ```
 * More at: https://exabyte.atlassian.net/wiki/display/PD/Combinatorial+materials+set
 */
/**
 * Regular expression for basis line.
 * @type {RegExp}
 */
// eslint-disable-next-line max-len
const LINE_REGEX = /^([A-Z][a-z]?\/?,?)+\s+(-?\d+\.?\d*|\.\d+)\s+(-?\d+\.?\d*|\.\d+)\s+(-?\d+\.?\d*|\.\d+)\s*$/gi;
// vacancy characters will be used to create vacancies on basis generation
const VACANCY_CHARACTER = "Vac";
const COMBINATION_DELIMITER = ",";
const PERMUTATION_DELIMITER = "/";
/**
 * Basis validation error codes.
 * @type {{MIXING_IN_SINGLE_LINE: number, MIXING_IN_MULTI_LINES: number, REGEX_NOT_PASSED: number}}
 */
const ERROR_CODES = {
    MIXING_IN_SINGLE_LINE: 1,
    MIXING_IN_MULTI_LINES: 2,
    REGEX_NOT_PASSED: 3,
};
class WrongBasisFormat extends Error {
    constructor(xyz, message, code) {
        super(message);
        this.xyz = xyz;
        console.log(`Wrong basis format: ${message}, code: ${code}`);
    }
}
exports.WrongBasisFormat = WrongBasisFormat;
class CombinatorialBasis {
    constructor(eXYZ) {
        this._xyz = eXYZ;
        this._lines = s
            .lines(eXYZ)
            .map((x) => x.trim())
            .filter((x) => x !== "")
            .map(this._parseBasisLine);
        this._hasPermutationLine = this._lines.reduce((mem, a) => {
            return mem || a.isPermutation;
        }, false);
        this._hasCombinationLine = this._lines.reduce((mem, a) => {
            return mem || a.isCombination;
        }, false);
        if (this._hasPermutationLine && this._hasCombinationLine) {
            throw new WrongBasisFormat(this._xyz, "Basis contains mixed permutation and combination.", ERROR_CODES.MIXING_IN_MULTI_LINES);
        }
    }
    /**
     * Parses combinatorial basis line and returns result as Object. Throws exception if line is not valid:
     * - does not meet RegExp
     * - mixes permutation and combination
     * @param str {String} Combinatorial basis' line
     * @param index {Number} order of the
     * @return {{displayName: string, isCombination: boolean, isPermutation: boolean, elements: Array, coordinates: *[]}}
     * @private
     */
    _parseBasisLine(str, index) {
        if (!str.match(LINE_REGEX)) {
            throw new WrongBasisFormat(this._xyz, `Line #${index + 1}: "${str}" contains errors. ` +
                'Allowed formats: "Si 0 0 0", "Si/Li 0.5 0.5 0.5", "Si,Ge 0.7 0.7 0.8"', ERROR_CODES.REGEX_NOT_PASSED);
        }
        const containsPermutation = str.indexOf(PERMUTATION_DELIMITER) > -1;
        const containsCombination = str.indexOf(COMBINATION_DELIMITER) > -1;
        if (containsCombination && containsPermutation) {
            throw new WrongBasisFormat(this._xyz, `Line #${index} contains mixed permutation and combination.`, ERROR_CODES.MIXING_IN_SINGLE_LINE);
        }
        let elements = [];
        const words = s
            .words(str)
            .map((x) => x.trim())
            .filter((x) => x != null);
        if (containsCombination) {
            elements = words[0].split(COMBINATION_DELIMITER).map((x) => x.trim());
        }
        else if (containsPermutation) {
            elements = words[0].split(PERMUTATION_DELIMITER).map((x) => x.trim());
        }
        else {
            elements = [words[0]];
        }
        const coordinate = [parseFloat(words[1]), parseFloat(words[2]), parseFloat(words[3])];
        return {
            // TODO: define as a type
            displayName: `ELEMENT_${index}`,
            isCombination: containsCombination,
            isPermutation: containsPermutation,
            elements,
            coordinate,
        };
    }
    /**
     * Returns array of ALL unique elements used in basis.
     * @return {String[]}
     */
    get uniqueElements() {
        return (0, lodash_1.chain)(this._lines)
            .map((line) => line.elements)
            .flatten()
            .uniq()
            .value()
            .sort();
    }
    static toBasisConfigForElementsAndCoordinates(array, units = "crystal", cell = new cell_1.Cell()) {
        return {
            elements: (0, lodash_1.map)(array, "element"),
            coordinates: (0, lodash_1.map)(array, "coordinate"),
            units,
            cell,
        };
    }
    /**
     * Returns array of regular bases extracted from current combinatorial basis.
     * @return {Basis[]|Object[]}
     */
    get allBasisConfigs() {
        let result = [];
        if (this._hasPermutationLine) {
            result = this._permutation();
        }
        else if (this._hasCombinationLine) {
            result = this._combination();
        }
        else {
            const items = [];
            this._lines.forEach((line) => {
                items.push({
                    element: line.elements[0],
                    coordinate: line.coordinate,
                });
            });
            result = [items];
        }
        return result.map((x) => CombinatorialBasis.toBasisConfigForElementsAndCoordinates(x));
    }
    /**
     * Returns array of regular bases extracted from current combinatorial basis with combinations.
     * @private
     */
    _combination() {
        const dimensions = [];
        this._lines.forEach((line) => {
            const itemsSet = [];
            line.elements.forEach((element) => {
                // omit vacancy characters
                itemsSet.push({
                    element,
                    coordinate: line.coordinate,
                });
            });
            dimensions.push(itemsSet);
        });
        // @ts-ignore // We're multiplying objects with math, not numbers. No type casting will help.
        const basisSet = math_1.math.cartesianProduct.apply(null, dimensions);
        return basisSet.map((basis) => basis.filter((entry) => entry.element !== VACANCY_CHARACTER));
    }
    /**
     * Returns array of regular bases extracted from current combinatorial basis with permutations.
     * @return {Basis[]}
     * @private
     */
    _permutation() {
        const maxLen = Math.max(...this._lines.map((x) => x.elements.length));
        const bases = [];
        for (let i = 0; i < maxLen; i++) {
            const items = [];
            this._lines.forEach((line) => {
                const element = line.elements.length <= i ? (0, lodash_1.last)(line.elements) : line.elements[i];
                if (element !== VACANCY_CHARACTER) {
                    items.push({
                        element,
                        coordinate: line.coordinate,
                    });
                }
            });
            bases.push(items);
        }
        return bases;
    }
    /**
     * Returns true if current combinatorial basis contains more than one regular basis.
     * @return {Boolean}
     */
    isCombinatorial() {
        return this._hasCombinationLine || this._hasPermutationLine;
    }
}
exports.CombinatorialBasis = CombinatorialBasis;
