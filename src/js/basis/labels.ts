import { ArrayWithIds } from "@mat3ra/code";
import { AtomicLabelsPropertySchema } from "@mat3ra/esse/dist/js/types";

export type AtomicLabelValue = AtomicLabelsPropertySchema["values"][number]["value"];

export class Labels extends ArrayWithIds<AtomicLabelValue> {}
