import { ArrayWithIds } from "@mat3ra/code";
import { AtomicFloatSchema } from "@mat3ra/esse/dist/js/types";

export type AtomicMagneticMomentValue = AtomicFloatSchema["value"];

export class MagneticMoments extends ArrayWithIds<AtomicMagneticMomentValue> {}
