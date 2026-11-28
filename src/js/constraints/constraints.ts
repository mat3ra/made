import { ArrayWithIds, ValueWithId } from "@mat3ra/code";
import { AtomicConstraintSchema, AtomicConstraintsSchema } from "@mat3ra/esse/dist/js/types";

export type AtomicConstraintValue = AtomicConstraintSchema["value"];

export class Constraint extends ValueWithId<AtomicConstraintValue> {
    value: AtomicConstraintValue;

    constructor({ value, id }: AtomicConstraintSchema) {
        super({ id, value });
        this.value = value;
    }

    getValueAsString(): string {
        return this.value.map((x) => (x ? 1 : 0)).join(" ");
    }

    prettyPrint(): string {
        return this.value.map((x) => (x ? 1 : 0)).join(" ");
    }

    // By default, the constraint is unconstrained if all values are 1/true.
    isUnconstrained(): boolean {
        return this.value.every((val) => val);
    }
}

export class AtomicConstraints extends ArrayWithIds<AtomicConstraintValue> {
    get areUnconstrained(): boolean {
        return this.values.every((constraint) => {
            const _constraint = Constraint.fromValueAndId(constraint);
            return _constraint.isUnconstrained();
        });
    }

    override toJSON(): AtomicConstraintsSchema {
        return super.toJSON() as AtomicConstraintsSchema;
    }
}
