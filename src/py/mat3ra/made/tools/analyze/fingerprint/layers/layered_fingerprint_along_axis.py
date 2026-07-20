from itertools import cycle, islice
from typing import List

from mat3ra.esse.models.core.reusable.axis_enum import AxisEnum
from mat3ra.made.tools.analyze.fingerprint.layers.unique_element_string_per_layer import UniqueElementStringsPerLayer
from mat3ra.utils.array import jaccard_similarity_for_strings
from pydantic import BaseModel, Field


class LayeredFingerprintAlongAxis(BaseModel):
    layers: List[UniqueElementStringsPerLayer] = Field(default_factory=list, description="List of layer fingerprints")
    axis: AxisEnum = Field(default=AxisEnum.z, description="Axis along which the fingerprint is computed")
    layer_thickness: float = Field(default=1.0, gt=0, description="Thickness of each layer in Angstroms")

    @property
    def non_empty_layers(self) -> List[UniqueElementStringsPerLayer]:
        return [layer for layer in self.layers if layer.elements]

    @property
    def element_sequence(self) -> List[List[str]]:
        return [layer.elements for layer in self.layers]

    def get_similarity_score(self, other: "LayeredFingerprintAlongAxis") -> float:
        """
        Calculate Jaccard similarity score between this and another fingerprint.

        The Jaccard similarity coefficient measures the similarity between two sets by comparing
        the size of their intersection to the size of their union: J(A, B) = |A ∩ B| / |A ∪ B|.
        In this implementation, we compare the sets of chemical elements in corresponding layers
        between two fingerprints. For example, if layer 1 contains {Si, O} and the corresponding
        layer contains {Si, Ge}, the Jaccard score is 1/3 (one common element divided by three
        unique elements total). The final score is the average across all layers, providing a
        measure of compositional similarity along the axis (0.0 = completely different,
        1.0 = identical composition in all layers).

        Args:
            other: Another LayeredFingerprintAlongAxis to compare with

        Returns:
            float: Average Jaccard similarity score (0.0 to 1.0). Returns 0.0 if the number of layers doesn't match.
        """
        if not self.layers or not other.layers:
            return 0.0
        if len(self.layers) != len(other.layers):
            return 0.0

        seq1, seq2 = self.element_sequence, other.element_sequence
        return sum(jaccard_similarity_for_strings(a, b) for a, b in zip(seq1, seq2)) / len(seq1)

    def get_similarity_score_ignore_periodicity(self, other: "LayeredFingerprintAlongAxis") -> float:
        """
        Calculate Jaccard similarity score ignoring periodicity differences.

        Handles cases where one fingerprint is a periodic repetition of another.
        For example, if self has 6 layers and other has 2 layers, this method checks if
        self.layers is a 3× repetition of other.layers (i.e., layers 0–1 match other,
        layers 2–3 match other, etc.).

        Args:
            other: Another LayeredFingerprintAlongAxis to compare with

        Returns:
            float: Average Jaccard similarity score (0.0 to 1.0). Returns 0.0 if the number
                   of layers is not a multiple relationship or if fingerprints don't match.
        """
        if not self.layers or not other.layers:
            return 0.0

        len_a, len_b = len(self.layers), len(other.layers)
        if len_a == len_b:
            return self.get_similarity_score(other)

        # Identify shorter/longer and ensure multiplicity
        if len_a < len_b:
            short_seq, long_seq = self.element_sequence, other.element_sequence
        else:
            short_seq, long_seq = other.element_sequence, self.element_sequence

        if len(long_seq) % len(short_seq) != 0:
            return 0.0

        cycled_short = islice(cycle(short_seq), len(long_seq))
        return sum(jaccard_similarity_for_strings(a, b) for a, b in zip(cycled_short, long_seq)) / len(short_seq)
