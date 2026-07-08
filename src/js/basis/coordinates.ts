import { RoundedArrayWithIds, RoundedValueWithId, RoundedVector3D, Vector3D } from "@mat3ra/code";
import {
    AtomicCoordinateSchema,
    Coordinate3DSchema,
    Matrix3X3Schema,
    Vector3DSchema,
} from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";
import { sprintf } from "underscore.string";


export type AtomicCoordinateValue = AtomicCoordinateSchema["value"];

type AxisType = "x" | "y" | "z";

export class Coordinate extends RoundedValueWithId<AtomicCoordinateValue> {
    value: AtomicCoordinateValue;

    constructor({ value, id }: AtomicCoordinateSchema) {
        super(id, value);
        this.value = value;
    }

    getValueAlongAxis(axis: AxisType = "z"): number {
        const index = { x: 0, y: 1, z: 2 }[axis];
        return this.value[index] as number;
    }

    translateByVector(vectorAsArray: Vector3DSchema): Coordinate {
        const vector3D = new Vector3D(this.value);
        this.value = vector3D.translateByVector(vectorAsArray).value;
        return this;
    }

    get valueRounded(): number[] {
        return new RoundedVector3D(this.value).valueRounded;
    }

    getValueRoundedWithPrecision(precision: number): number[] {
        const RoundedInstance = RoundedVector3D;
        RoundedInstance.roundPrecision = precision;
        return new RoundedInstance(this.value).valueRounded;
    }

    prettyPrint(format = "%14.9f", precision: number = this.precision): string {
        return this.getValueRoundedWithPrecision(precision)
            .map((x) => sprintf(format, x))
            .join(" ");
    }
}

export class Coordinates extends RoundedArrayWithIds<Coordinate3DSchema> {
    getValuesAlongAxis(axis: AxisType = "z"): number[] {
        return this.values.map((coord) => {
            const coordinate = Coordinate.fromValueAndId(coord);
            return coordinate.getValueAlongAxis(axis);
        });
    }

    getMaxValueAlongAxis(axis: AxisType = "z"): number {
        return Math.max(...this.getValuesAlongAxis(axis));
    }

    getMinValueAlongAxis(axis: AxisType = "z"): number {
        return Math.min(...this.getValuesAlongAxis(axis));
    }

    getExtremumValueAlongAxis(extremum: "max" | "min" = "max", axis: AxisType = "z"): number {
        return extremum === "max"
            ? this.getMaxValueAlongAxis(axis)
            : this.getMinValueAlongAxis(axis);
    }

    translateByVector(vector: Vector3DSchema): void {
        this.mapArrayInPlace((x) => {
            const coordinate = Coordinate.fromValueAndId(x);
            return coordinate.translateByVector(vector).value;
        });
    }

    getCenterPoint(): Vector3DSchema {
        const transposed = Utils.math.transpose(this.values) as Matrix3X3Schema;
        const center: Vector3DSchema = [0, 0, 0];

        for (let i = 0; i < 3; i++) {
            const axisCoords = transposed[i] as Coordinate3DSchema;
            const sum = axisCoords.reduce((a, b) => a + b, 0);
            center[i] = sum / this.values.length;
        }

        return center;
    }
}
