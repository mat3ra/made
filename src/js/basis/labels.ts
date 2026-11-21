import { ArrayWithIds } from "@mat3ra/code";
import { AtomicLabelSchema } from "@mat3ra/esse/dist/js/types";

export type AtomicLabelValue = AtomicLabelSchema["value"];

export class Labels extends ArrayWithIds<AtomicLabelValue> {}
