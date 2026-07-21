import type { MaterialSchema } from "@mat3ra/esse/dist/js/types";
import { Utils } from "@mat3ra/utils";

import { Material } from "../../../src/js/material";
import tools from "../../../src/js/tools";
import { SlabConfigSchema } from "../../../src/js/tools/surface";
import { Silicon, SiSlab100, SiSlab111, SiSlab111NoVacuum } from "../fixtures";

const { assertDeepAlmostEqual } = Utils.assertion;

const toJSONWithoutHash = (material: Material) => {
    return material.toJSON();
};

const generateSlabWithVacuum = (slabConfig: SlabConfigSchema, vacuumRatio: number) => {
    const slabMaterial = new Material(slabConfig);
    const { outOfPlaneAxisIndex } = slabConfig;
    const AXES = ["a", "b", "c"] as const;

    tools.material.scaleOneLatticeVector(
        slabMaterial,
        AXES[outOfPlaneAxisIndex],
        1 / (1 - vacuumRatio),
    );

    return slabMaterial;
};

describe("Tools:Surface", () => {
    it("should return slab (100)", () => {
        const material = new Material(Silicon);
        const slabConfig = tools.surface.generateConfig(material, [1, 0, 0], 3, 1, 1);
        assertDeepAlmostEqual(SiSlab100, slabConfig);
    });

    it("should return slab (111)", () => {
        const material = new Material(Silicon);
        const slabConfig = tools.surface.generateConfig(material, [1, 1, 1], 3, 1, 1);
        assertDeepAlmostEqual(SiSlab111NoVacuum, slabConfig);
    });

    it("should return slab (111) even if ids shifted", () => {
        const adjustedSilicon: MaterialSchema = {
            ...Silicon,
            basis: {
                elements: [
                    {
                        id: 10,
                        value: "Si",
                    },
                    {
                        id: 14,
                        value: "Si",
                    },
                ],
                coordinates: [
                    {
                        id: 10,
                        value: [0.0, 0.0, 0.0],
                    },
                    {
                        id: 14,
                        value: [0.25, 0.25, 0.25],
                    },
                ],
            },
        };
        const material = new Material(adjustedSilicon);
        const slabConfig = tools.surface.generateConfig(material, [1, 1, 1], 3, 1, 1);
        assertDeepAlmostEqual(SiSlab111NoVacuum, slabConfig);
    });

    it("should return slab (111) with vacuum", () => {
        const material = new Material(Silicon);
        const slabConfig = tools.surface.generateConfig(material, [1, 1, 1], 3, 1, 1);
        const vacuumRatio = 0.5;
        const slabMaterial = generateSlabWithVacuum(slabConfig, vacuumRatio);
        const expectedSlabMaterial = new Material(SiSlab111);
        const expectedMaterialJSON = expectedSlabMaterial.toJSON();
        const slabMaterialJSON = slabMaterial.toJSON();
        assertDeepAlmostEqual(expectedMaterialJSON, slabMaterialJSON);
    });

    it("should return slab (111) with vacuum for gamma = 59.999", () => {
        const adjustedSilicon = {
            ...Silicon,
            lattice: {
                ...Silicon.lattice,
                gamma: 59.999,
            },
        };
        const material = new Material(adjustedSilicon);
        const slabConfig = tools.surface.generateConfig(material, [1, 1, 1], 3, 1, 1);
        const vacuumRatio = 0.5;
        const slabMaterial = generateSlabWithVacuum(slabConfig, vacuumRatio);
        const expectedSlabMaterial = new Material(SiSlab111);
        assertDeepAlmostEqual(
            toJSONWithoutHash(expectedSlabMaterial),
            toJSONWithoutHash(slabMaterial),
        );
    });

    it("should return slab (111) with vacuum for gamma = 60.001", () => {
        const adjustedSilicon = {
            ...Silicon,
            lattice: {
                ...Silicon.lattice,
                gamma: 60.001,
            },
        };
        const material = new Material(adjustedSilicon);
        const slabConfig = tools.surface.generateConfig(material, [1, 1, 1], 3, 1, 1);
        const vacuumRatio = 0.5;
        const slabMaterial = generateSlabWithVacuum(slabConfig, vacuumRatio);
        const expectedSlabMaterial = new Material(SiSlab111);
        assertDeepAlmostEqual(
            toJSONWithoutHash(expectedSlabMaterial),
            toJSONWithoutHash(slabMaterial),
        );
    });
});
