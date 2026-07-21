import { type MaterialSchema, Coordinate3DSchema } from "@mat3ra/esse/dist/js/types";
import { type MaterialConfig, Material } from "../material";
export type SlabConfigSchema = MaterialConfig & {
    outOfPlaneAxisIndex: number;
};
declare function generateConfig<S extends MaterialSchema = MaterialSchema>(material: Material<S>, millerIndices: Coordinate3DSchema, numberOfLayers?: number, vx?: number, vy?: number): SlabConfigSchema;
declare const _default: {
    generateConfig: typeof generateConfig;
};
export default _default;
