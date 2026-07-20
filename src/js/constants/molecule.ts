/**
 * Constants for molecule handling and precision.
 * Source of truth: /constants.json at repository root
 *
 * These values are duplicated here for TypeScript compilation.
 * When updating these, also update constants.json.
 */

export const defaultNonPeriodicMinimumLatticeSize = 3.0;
export const diatomicLatticePaddingFactor = 3.0;
export const molecularLatticePaddingFactor = 2.0;

export const PRECISION_MAP = {
    coordinatesCrystal: 9,
    coordinatesCartesian: 6,
    latticeLengths: 6,
    latticeAngles: 4,
};
