declare const _default: {
    surface: {
        generateConfig: <S extends import("@mat3ra/esse/dist/js/types").MaterialSchema = import("@mat3ra/esse/dist/js/types").MaterialSchema>(material: import("../material").Material<S>, millerIndices: import("@mat3ra/esse/dist/js/types").Coordinate3DSchema, numberOfLayers?: number, vx?: number, vy?: number) => import("./surface").SlabConfigSchema;
    };
    supercell: {
        generateConfig: <S extends import("@mat3ra/esse/dist/js/types").MaterialSchema = import("@mat3ra/esse/dist/js/types").MaterialSchema>(material: import("../material").Material<S>, supercellMatrix: import("@mat3ra/esse/dist/js/types").Matrix3X3Schema) => {
            name: string;
            basis: import("@mat3ra/esse/dist/js/types").BasisSchema;
            lattice: import("@mat3ra/esse/dist/js/types").LatticeSchema;
        };
        generateNewBasisWithinSupercell: (basis: import("../made").Basis | import("../basis/constrained_basis").ConstrainedBasis, cell: import("../made").Cell, supercell: import("../made").Cell, supercellMatrix: import("@mat3ra/esse/dist/js/types").Matrix3X3Schema) => import("../made").Basis;
    };
    material: {
        scaleOneLatticeVector: (material: import("../material").Material, key?: "a" | "b" | "c", factor?: number) => void;
        scaleLatticeToMakeNonPeriodic: (material: import("../material").Material) => void;
        translateAtomsToCenter: (material: import("../material").Material) => void;
    };
    basis: {
        repeat: (basis: import("../made").Basis, repetitions: number[]) => import("../made").Basis;
        interpolate: (initialBasis: import("../made").Basis, finalBasis: import("../made").Basis, numberOfSteps?: number) => import("../made").Basis[];
    };
};
export default _default;
