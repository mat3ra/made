import type { InMemoryEntity } from "@mat3ra/code/dist/js/entity";
import type { MaterialPropertiesSchema } from "@mat3ra/esse/dist/js/types";

export type MaterialSchemaMixin = MaterialPropertiesSchema;

export type MaterialInMemoryEntity = InMemoryEntity & MaterialSchemaMixin;

export function materialSchemaMixin<T extends InMemoryEntity>(
    item: InMemoryEntity,
): asserts item is T & MaterialSchemaMixin {
    // @ts-expect-error
    const properties: InMemoryEntity<MaterialSchemaMixin> & MaterialSchemaMixin = {
        get formula() {
            return this.prop("formula");
        },
        set formula(value: MaterialPropertiesSchema["formula"]) {
            this.setProp("formula", value);
        },
        get unitCellFormula() {
            return this.prop("unitCellFormula");
        },
        set unitCellFormula(value: MaterialPropertiesSchema["unitCellFormula"]) {
            this.setProp("unitCellFormula", value);
        },
        get basis() {
            return this.requiredProp("basis");
        },
        set basis(value: MaterialPropertiesSchema["basis"]) {
            this.setProp("basis", value);
        },
        get lattice() {
            return this.requiredProp("lattice");
        },
        set lattice(value: MaterialPropertiesSchema["lattice"]) {
            this.setProp("lattice", value);
        },
        get derivedProperties() {
            return this.prop("derivedProperties");
        },
        set derivedProperties(value: MaterialPropertiesSchema["derivedProperties"]) {
            this.setProp("derivedProperties", value);
        },
        get external() {
            return this.prop("external");
        },
        set external(value: MaterialPropertiesSchema["external"]) {
            this.setProp("external", value);
        },
        get src() {
            return this.prop("src");
        },
        set src(value: MaterialPropertiesSchema["src"]) {
            this.setProp("src", value);
        },
        get scaledHash() {
            return this.prop("scaledHash");
        },
        set scaledHash(value: MaterialPropertiesSchema["scaledHash"]) {
            this.setProp("scaledHash", value);
        },
        get icsdId() {
            return this.prop("icsdId");
        },
        set icsdId(value: MaterialPropertiesSchema["icsdId"]) {
            this.setProp("icsdId", value);
        },
        get isNonPeriodic() {
            return this.prop("isNonPeriodic");
        },
        set isNonPeriodic(value: MaterialPropertiesSchema["isNonPeriodic"]) {
            this.setProp("isNonPeriodic", value);
        },
        get consistencyChecks() {
            return this.prop("consistencyChecks");
        },
        set consistencyChecks(value: MaterialPropertiesSchema["consistencyChecks"]) {
            this.setProp("consistencyChecks", value);
        },
    };

    Object.defineProperties(item, Object.getOwnPropertyDescriptors(properties));
}
