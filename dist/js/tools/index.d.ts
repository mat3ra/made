declare const _default: {
    surface: {
        generateConfig: <Schemas extends import("../Material").MaterialSchemaMap = import("../Material").MaterialSchemaMap>(material: import("../Material").default<Schemas>, millerIndices: import("@mat3ra/esse/dist/js/types").Coordinate3DSchema, numberOfLayers?: number, vx?: number, vy?: number) => import("./surface").SlabConfigSchema;
    };
    supercell: {
        generateConfig: <Schemas extends import("../Material").MaterialSchemaMap = import("../Material").MaterialSchemaMap>(material: import("../Material").default<Schemas>, supercellMatrix: import("@mat3ra/esse/dist/js/types").Matrix3X3Schema) => {
            name: string;
            basis: import("../basis/basis").BasisConfig & import("@mat3ra/esse/dist/js/types").BaseInMemoryEntitySchema;
            lattice: import("@mat3ra/esse/dist/js/types").LatticeSchema;
        };
        generateNewBasisWithinSupercell: (basis: import("../made").Basis | import("../basis/constrained_basis").ConstrainedBasis, cell: import("../made").Cell, supercell: import("../made").Cell, supercellMatrix: import("@mat3ra/esse/dist/js/types").Matrix3X3Schema) => import("../made").Basis;
    };
    material: {
        scaleOneLatticeVector: (material: import("../Material").default, key?: "a" | "b" | "c", factor?: number) => void;
        scaleLatticeToMakeNonPeriodic: (material: import("../Material").default) => void;
        translateAtomsToCenter: (material: import("../Material").default) => void;
    };
    basis: {
        repeat: (basis: import("../made").Basis, repetitions: number[]) => import("../made").Basis;
        interpolate: (initialBasis: import("../made").Basis, finalBasis: import("../made").Basis, numberOfSteps?: number) => import("../made").Basis<import("../basis/basis").BasisConfig>[];
    };
};
export default _default;
