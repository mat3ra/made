import { Basis } from "../basis/basis";
/**
 * Returns a repeated basis of a crystal.
 * @param basis {Basis} Original basis.
 * @param repetitions{Number[]} Repetition vector `[x, y, z]`, in each spatial dimension.
 * @return {Basis} New Basis.
 */
declare function repeat(basis: Basis, repetitions: number[]): Basis;
/**
 * Returns a set of Bases for a crystal interpolated from initial to final crystal.
 *          Can be used to generate atomic configurations along a chemical reaction path, for example.
 * @param initialBasis {Basis} Original initialBasis.
 * @param finalBasis {Basis} Final initialBasis.
 * @param numberOfSteps{Number} Number of intermediate steps.
 * @return {Basis[]} List of all bases.
 */
declare function interpolate(initialBasis: Basis, finalBasis: Basis, numberOfSteps?: number): Basis<import("../basis/basis").BasisConfig>[];
declare const _default: {
    repeat: typeof repeat;
    interpolate: typeof interpolate;
};
export default _default;
