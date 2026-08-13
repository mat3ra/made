import { Coordinate3DSchema } from "@mat3ra/esse/dist/js/types";
import Material, { type MaterialConfig, type MaterialSchemaMap } from "../Material";
export type SlabConfigSchema = MaterialConfig & {
    outOfPlaneAxisIndex: number;
};
declare function generateConfig<Schemas extends MaterialSchemaMap = MaterialSchemaMap>(material: Material<Schemas>, millerIndices: Coordinate3DSchema, numberOfLayers?: number, vx?: number, vy?: number): SlabConfigSchema;
declare const _default: {
    generateConfig: typeof generateConfig;
};
export default _default;
