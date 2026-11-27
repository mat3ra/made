import { ArrayWithIds, ValueWithId } from "@mat3ra/code";
import { AtomicConstraintSchema } from "@mat3ra/esse/dist/js/types";

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
    /**
     * Get constraints for an atom with index as string.
     * @param idx - atom index.
     * @param mapFn (OPTIONAL) - a function to be applied to each constraint. By default 0 or 1 is returned.
     */
    getAsStringByIndex(idx: number, mapFn = (val: boolean): string => (val ? "1" : "0")): string {
        const constraints = this.getElementValueByIndex(idx);
        return constraints ? constraints.map(mapFn).join(" ") : "";
    }

    get areUnconstrained(): boolean {
        return this.values.every((constraint) => {
            const _constraint = Constraint.fromValueAndId(constraint);
            return _constraint.isUnconstrained();
        });
    }
}
