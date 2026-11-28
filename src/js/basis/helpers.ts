import s from "underscore.string";

import { AtomicElementValue } from "./elements";
import { AtomicLabelValue } from "./labels";

export class ElementWithLabel {
    element: AtomicElementValue;

    label?: AtomicLabelValue;

    constructor({ element, label }: { element: AtomicElementValue; label?: AtomicLabelValue }) {
        this.element = element;
        this.label = label;
    }

    prettyPrint(): string {
        const elementWithLabel = `${this.element}${this.label ?? ""}`;
        return s.sprintf("%-3s", elementWithLabel);
    }
}
