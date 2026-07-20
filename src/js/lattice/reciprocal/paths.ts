/**
 * Default k-point paths according to:
 *  [AFLOW](https://arxiv.org/abs/1004.2974) methodology.
 *  Paths are split in parts for clarity.
 *
 * Raw segment data is stored in data/reciprocal_paths.json (shared with Python).
 */
import points from "../../data/reciprocal_paths.json";

interface KPointStep {
    point: string;
    steps: number;
}

interface PathsType {
    [key: string]: KPointStep[];
}

// Export a processed version of the paths
export const paths: PathsType = (() => {
    const result: PathsType = {};

    Object.entries(points).forEach(([key, pathSegments]) => {
        // Flatten arrays of path segments into a single array
        const flattenedPath: string[] = pathSegments.reduce(
            (acc, segment) => [...acc, ...segment],
            [] as string[],
        );

        // Convert to KPointStep array
        // TODO: calculate number of steps based on distance in k-space
        result[key] = flattenedPath.map((point) => ({
            point,
            steps: 10,
        }));
    });

    return result;
})();
