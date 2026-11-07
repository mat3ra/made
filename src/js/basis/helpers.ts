import s from "underscore.string";

import { AtomicElementValue } from "./elements";

export class ElementWithLabel {
    element: AtomicElementValue;

    label: string;

    constructor({ element, label }: { element: AtomicElementValue; label: string }) {
        this.element = element;
        this.label = label;
    }

    prettyPrint(): string {
        const elementWithLabel = `${this.element}${this.label}`;
        return s.sprintf("%-3s", elementWithLabel);
    }
}
