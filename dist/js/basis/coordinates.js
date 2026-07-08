"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Coordinates = exports.Coordinate = void 0;
const code_1 = require("@mat3ra/code");
const utils_1 = require("@mat3ra/utils");
const underscore_string_1 = require("underscore.string");
class Coordinate extends code_1.RoundedValueWithId {
    constructor({ value, id }) {
        super(id, value);
        this.value = value;
    }
    getValueAlongAxis(axis = "z") {
        const index = { x: 0, y: 1, z: 2 }[axis];
        return this.value[index];
    }
    translateByVector(vectorAsArray) {
        const vector3D = new code_1.Vector3D(this.value);
        this.value = vector3D.translateByVector(vectorAsArray).value;
        return this;
    }
    get valueRounded() {
        return new code_1.RoundedVector3D(this.value).valueRounded;
    }
    getValueRoundedWithPrecision(precision) {
        const RoundedInstance = code_1.RoundedVector3D;
        RoundedInstance.roundPrecision = precision;
        return new RoundedInstance(this.value).valueRounded;
    }
    prettyPrint(format = "%14.9f", precision = this.precision) {
        return this.getValueRoundedWithPrecision(precision)
            .map((x) => (0, underscore_string_1.sprintf)(format, x))
            .join(" ");
    }
}
exports.Coordinate = Coordinate;
class Coordinates extends code_1.RoundedArrayWithIds {
    getValuesAlongAxis(axis = "z") {
        return this.values.map((coord) => {
            const coordinate = Coordinate.fromValueAndId(coord);
            return coordinate.getValueAlongAxis(axis);
        });
    }
    getMaxValueAlongAxis(axis = "z") {
        return Math.max(...this.getValuesAlongAxis(axis));
    }
    getMinValueAlongAxis(axis = "z") {
        return Math.min(...this.getValuesAlongAxis(axis));
    }
    getExtremumValueAlongAxis(extremum = "max", axis = "z") {
        return extremum === "max"
            ? this.getMaxValueAlongAxis(axis)
            : this.getMinValueAlongAxis(axis);
    }
    translateByVector(vector) {
        this.mapArrayInPlace((x) => {
            const coordinate = Coordinate.fromValueAndId(x);
            return coordinate.translateByVector(vector).value;
        });
    }
    getCenterPoint() {
        const transposed = utils_1.Utils.math.transpose(this.values);
        const center = [0, 0, 0];
        for (let i = 0; i < 3; i++) {
            const axisCoords = transposed[i];
            const sum = axisCoords.reduce((a, b) => a + b, 0);
            center[i] = sum / this.values.length;
        }
        return center;
    }
}
exports.Coordinates = Coordinates;
