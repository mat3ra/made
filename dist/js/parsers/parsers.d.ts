declare const _default: {
    xyz: {
        validate: typeof import("./xyz").validate;
        fromMaterial: (materialOrConfig: import("@mat3ra/esse/dist/js/types").MaterialSchema | import("@mat3ra/esse/dist/js/types").MaterialEnhancedSchema, fractional?: boolean) => string;
        toBasisConfig: (txt: string, units?: string, cell?: import("../made").Cell) => import("../basis/constrained_basis").ConstrainedBasisConfig;
        fromBasis: (basisClsInstance: import("../basis/constrained_basis").ConstrainedBasis, coordinatePrintFormat: string) => string;
        CombinatorialBasis: typeof import("./xyz_combinatorial_basis").CombinatorialBasis;
    };
    poscar: {
        isPoscar: (text: string) => boolean;
        toPoscar: (materialOrConfig: import("@mat3ra/esse/dist/js/types").MaterialSchema | import("@mat3ra/esse/dist/js/types").MaterialEnhancedSchema, omitConstraints?: boolean) => string;
        fromPoscar: (fileContent: string) => import("../Material").MaterialConfig;
        atomicConstraintsCharFromBool: (bool: boolean) => string;
        atomsCount: typeof import("./poscar").atomsCount;
    };
    cif: {
        parseMeta: (txt: string) => import("./cif").Meta;
    };
    espresso: {
        toEspressoFormat: (materialOrConfig: import("@mat3ra/esse/dist/js/types").MaterialSchema | import("@mat3ra/esse/dist/js/types").MaterialEnhancedSchema) => string;
    };
    nativeFormatParsers: {
        detectFormat: (text: string) => "json" | "poscar" | "unknown";
        convertFromNativeFormat: (text: string) => import("../Material").MaterialConfig;
    };
};
export default _default;
