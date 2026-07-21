"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.materialSchemaMixin = materialSchemaMixin;
function materialSchemaMixin(item) {
    // @ts-expect-error
    const properties = {
        get formula() {
            return this.prop("formula");
        },
        set formula(value) {
            this.setProp("formula", value);
        },
        get unitCellFormula() {
            return this.prop("unitCellFormula");
        },
        set unitCellFormula(value) {
            this.setProp("unitCellFormula", value);
        },
        get basis() {
            return this.requiredProp("basis");
        },
        set basis(value) {
            this.setProp("basis", value);
        },
        get lattice() {
            return this.requiredProp("lattice");
        },
        set lattice(value) {
            this.setProp("lattice", value);
        },
        get derivedProperties() {
            return this.prop("derivedProperties");
        },
        set derivedProperties(value) {
            this.setProp("derivedProperties", value);
        },
        get external() {
            return this.prop("external");
        },
        set external(value) {
            this.setProp("external", value);
        },
        get src() {
            return this.prop("src");
        },
        set src(value) {
            this.setProp("src", value);
        },
        get scaledHash() {
            return this.prop("scaledHash");
        },
        set scaledHash(value) {
            this.setProp("scaledHash", value);
        },
        get icsdId() {
            return this.prop("icsdId");
        },
        set icsdId(value) {
            this.setProp("icsdId", value);
        },
        get isNonPeriodic() {
            return this.prop("isNonPeriodic");
        },
        set isNonPeriodic(value) {
            this.setProp("isNonPeriodic", value);
        },
        get consistencyChecks() {
            return this.prop("consistencyChecks");
        },
        set consistencyChecks(value) {
            this.setProp("consistencyChecks", value);
        },
    };
    Object.defineProperties(item, Object.getOwnPropertyDescriptors(properties));
}
