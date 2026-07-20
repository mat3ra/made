import { Basis } from "./basis/basis";
import { Cell } from "./cell/cell";
import { ATOMIC_COORD_UNITS, coefficients, tolerance, units } from "./constants";
import { AtomicConstraints } from "./constraints/constraints";
import { defaultNonPeriodicMinimumLatticeSize, diatomicLatticePaddingFactor, Lattice, molecularLatticePaddingFactor } from "./lattice/lattice";
import { DEFAULT_LATTICE_UNITS, LATTICE_TYPE_CONFIGS } from "./lattice/lattice_types";
import { ReciprocalLattice } from "./lattice/reciprocal/lattice_reciprocal";
import { UnitCell } from "./lattice/unit_cell";
import { defaultMaterialConfig, Material } from "./material";
import parsers from "./parsers/parsers";
import tools from "./tools/index";
export declare const Made: {
    coefficients: {
        EV_TO_RY: number;
        BOHR_TO_ANGSTROM: number;
        ANGSTROM_TO_BOHR: number;
        EV_A_TO_RY_BOHR: number;
    };
    tolerance: {
        length: number;
        lengthAngstrom: number;
        pointsDistance: number;
    };
    units: {
        bohr: string;
        angstrom: string;
        degree: string;
        radian: string;
        alat: string;
    };
    ATOMIC_COORD_UNITS: {
        crystal: string;
        cartesian: string;
    };
    Material: typeof Material;
    defaultMaterialConfig: import("./material").MaterialConfig;
    Lattice: typeof Lattice;
    Cell: typeof Cell;
    UnitCell: typeof UnitCell;
    defaultNonPeriodicMinimumLatticeSize: number;
    diatomicLatticePaddingFactor: number;
    molecularLatticePaddingFactor: number;
    ReciprocalLattice: typeof ReciprocalLattice;
    Basis: typeof Basis;
    AtomicConstraints: typeof AtomicConstraints;
    parsers: {
        xyz: {
            validate: typeof import("./parsers/xyz").validate;
            fromMaterial: (materialOrConfig: import("@mat3ra/esse/dist/js/types").MaterialSchema, fractional?: boolean) => string;
            toBasisConfig: (txt: string, units?: string, cell?: Cell) => import("./basis/constrained_basis").ConstrainedBasisConfig;
            fromBasis: (basisClsInstance: import("./basis/constrained_basis").ConstrainedBasis, coordinatePrintFormat: string) => string;
            CombinatorialBasis: typeof import("./parsers/xyz_combinatorial_basis").CombinatorialBasis;
        };
        poscar: {
            isPoscar: (text: string) => boolean;
            toPoscar: (materialOrConfig: import("@mat3ra/esse/dist/js/types").MaterialSchema, omitConstraints?: boolean) => string;
            fromPoscar: (fileContent: string) => object;
            atomicConstraintsCharFromBool: (bool: boolean) => string;
            atomsCount: typeof import("./parsers/poscar").atomsCount;
        };
        cif: {
            parseMeta: (txt: string) => import("./parsers/cif").Meta;
        };
        espresso: {
            toEspressoFormat: (materialOrConfig: import("@mat3ra/esse/dist/js/types").MaterialSchema) => string;
        };
        nativeFormatParsers: {
            detectFormat: (text: string) => string;
            convertFromNativeFormat: (text: string) => any;
        };
    };
    tools: {
        surface: {
            generateConfig: (material: Material, millerIndices: import("@mat3ra/esse/dist/js/types").Coordinate3DSchema, numberOfLayers?: number, vx?: number, vy?: number) => import("./tools/surface").SlabConfigSchema;
        };
        supercell: {
            generateConfig: (material: Material, supercellMatrix: import("@mat3ra/esse/dist/js/types").Matrix3X3Schema) => {
                name: string;
                basis: import("@mat3ra/esse/dist/js/types").BasisSchema;
                lattice: import("@mat3ra/esse/dist/js/types").LatticeSchema;
            };
            generateNewBasisWithinSupercell: (basis: Basis | import("./basis/constrained_basis").ConstrainedBasis, cell: Cell, supercell: Cell, supercellMatrix: import("@mat3ra/esse/dist/js/types").Matrix3X3Schema) => Basis;
        };
        material: {
            scaleOneLatticeVector: (material: Material, key?: "a" | "b" | "c", factor?: number) => void;
            scaleLatticeToMakeNonPeriodic: (material: Material) => void;
            translateAtomsToCenter: (material: Material) => void;
        };
        basis: {
            repeat: (basis: Basis, repetitions: number[]) => Basis;
            interpolate: (initialBasis: Basis, finalBasis: Basis, numberOfSteps?: number) => Basis[];
        };
    };
    LATTICE_TYPE_CONFIGS: import("./lattice/lattice_types").LatticeTypeConfig[];
    DEFAULT_LATTICE_UNITS: {
        length: {
            angstrom: string;
        };
        angle: {
            degree: string;
        };
    };
};
export { coefficients, tolerance, units, ATOMIC_COORD_UNITS, Material, defaultMaterialConfig, Lattice, Cell, UnitCell, defaultNonPeriodicMinimumLatticeSize, diatomicLatticePaddingFactor, molecularLatticePaddingFactor, ReciprocalLattice, Basis, AtomicConstraints, parsers, tools, LATTICE_TYPE_CONFIGS, DEFAULT_LATTICE_UNITS, };
