import Material from "../Material";
/**
 * Scales one lattice vector for the given material
 * @param material {Material} The material acted upon.
 * @param key {String} Lattice vector key.
 * @param factor {Number} Float scaling factor.
 */
declare function scaleOneLatticeVector(material: Material, key?: "a" | "b" | "c", factor?: number): void;
/**
 * Updates the size of a materials lattice using the minimumLatticeSize function.
 * The new size of the material is calculated based on the materials basis.
 * @param material {Material}
 */
declare function scaleLatticeToMakeNonPeriodic(material: Material): void;
/**
 * Updates the basis of a material by translating the coordinates
 * so that the center of the material and lattice are aligned.
 * @param material {Material}
 * */
declare function translateAtomsToCenter(material: Material): void;
declare const _default: {
    scaleOneLatticeVector: typeof scaleOneLatticeVector;
    scaleLatticeToMakeNonPeriodic: typeof scaleLatticeToMakeNonPeriodic;
    translateAtomsToCenter: typeof translateAtomsToCenter;
};
export default _default;
