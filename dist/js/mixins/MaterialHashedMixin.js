"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.materialHashedMixin = materialHashedMixin;
const HashedSchemaMixin_1 = require("@mat3ra/code/dist/js/generated/HashedSchemaMixin");
/**
 * Adds hash accessors plus basis/lattice setters that keep `hash` in sync.
 * Composes {@link hashedSchemaMixin}.
 */
function materialHashedMixin(item) {
    (0, HashedSchemaMixin_1.hashedSchemaMixin)(item);
    // @ts-expect-error Mixin descriptor object: accessors use entity `this`.
    const properties = {
        get basis() {
            return this.requiredProp("basis");
        },
        set basis(value) {
            this.setProp("basis", value);
            this.updateHash();
        },
        get lattice() {
            return this.requiredProp("lattice");
        },
        set lattice(value) {
            this.setProp("lattice", value);
            this.updateHash();
        },
        updateHash() {
            this.hash = this.calculateHash("", false, this.isNonPeriodic);
        },
    };
    Object.defineProperties(item, Object.getOwnPropertyDescriptors(properties));
}
