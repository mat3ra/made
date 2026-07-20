"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.paths = void 0;
/**
 * Default k-point paths according to:
 *  [AFLOW](https://arxiv.org/abs/1004.2974) methodology.
 *  Paths are split in parts for clarity.
 *
 * Raw segment data is stored in data/reciprocal_paths.json (shared with Python).
 */
const reciprocal_paths_json_1 = __importDefault(require("../../data/reciprocal_paths.json"));
// Export a processed version of the paths
exports.paths = (() => {
    const result = {};
    Object.entries(reciprocal_paths_json_1.default).forEach(([key, pathSegments]) => {
        // Flatten arrays of path segments into a single array
        const flattenedPath = pathSegments.reduce((acc, segment) => [...acc, ...segment], []);
        // Convert to KPointStep array
        // TODO: calculate number of steps based on distance in k-space
        result[key] = flattenedPath.map((point) => ({
            point,
            steps: 10,
        }));
    });
    return result;
})();
