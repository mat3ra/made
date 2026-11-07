import { ArrayWithIds } from "@mat3ra/code";
import { AtomicStartingMagnetizationSchema } from "@mat3ra/esse/dist/js/types";

export type AtomicStartingMagnetizationValue = AtomicStartingMagnetizationSchema["value"];

export class StartingMagnetization extends ArrayWithIds<AtomicStartingMagnetizationValue> {}
