import { LatticeSchema, Vector3DSchema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";

import { ATOMIC_COORD_UNITS } from "../constants";
import { Lattice } from "../lattice/lattice";
import { Material } from "../material";


/**
 * Scales one lattice vector for the given material
 * @param material {Material} The material acted upon.
 * @param key {String} Lattice vector key.
 * @param factor {Number} Float scaling factor.
 */

function scaleOneLatticeVector(material: Material, key: "a" | "b" | "c" = "a", factor = 1.0) {
    const lattice = { ...material.lattice };
    if (lattice.vectors === undefined) {
        throw new Error("Lattice vectors are undefined");
    }
    lattice.vectors[key] = lattice.vectors![key].map((v) => v * factor) as Vector3DSchema;

    material.lattice = Lattice.fromVectors(lattice.vectors).toJSON();
}

/**
 * Updates the size of a materials lattice using the minimumLatticeSize function.
 * The new size of the material is calculated based on the materials basis.
 * @param material {Material}
 */
function scaleLatticeToMakeNonPeriodic(material: Material) {
    material.lattice = Lattice.fromConfigPartial({
        a: material.Basis.getMinimumLatticeSize(),
        type: "CUB",
    } as LatticeSchema).toJSON();
}

/**
 * Updates the basis of a material by translating the coordinates
 * so that the center of the material and lattice are aligned.
 * @param material {Material}
 * */
function translateAtomsToCenter(material: Material) {
    const originalUnits = material.Basis.units;
    material.toCartesian();
    const updatedBasis = material.Basis;
    const centerOfCoordinates = updatedBasis.centerOfCoordinatesPoint;
    const centerOfLattice = Utils.math.multiply(
        0.5,
        material.Lattice.vectorArrays.reduce((a, b) => Utils.math.add(a, b) as Vector3DSchema),
    );
    const translationVector = Utils.math.subtract(centerOfLattice, centerOfCoordinates);
    updatedBasis.translateByVector(translationVector as Vector3DSchema);
    material.setBasis(updatedBasis.toJSON());
    if (originalUnits !== ATOMIC_COORD_UNITS.cartesian) material.toCrystal();
}

export default {
    scaleOneLatticeVector,
    scaleLatticeToMakeNonPeriodic,
    translateAtomsToCenter,
};
