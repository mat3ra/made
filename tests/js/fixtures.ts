import { AtomicConstraintsSchema, BasisSchema, MaterialSchema } from "@mat3ra/esse/dist/js/types";
import { MaterialStandata } from "@mat3ra/standata";
import fs from "fs";
import path from "path";

import AsGeBasis_JSON from "../fixtures/AsGe-basis.json";
import atomicConstraints_JSON from "../fixtures/atomic-constraints.json";
import C2H4_JSON from "../fixtures/C2H4.json";
import C2H4Translated_JSON from "../fixtures/C2H4-translated.json";
import FeLiSiBasis_JSON from "../fixtures/FeLiSi-basis.json";
import FeO_JSON from "../fixtures/FeO.json";

import Ge2Basis_JSON from "../fixtures/Ge2-basis.json";
import Graphene_JSON from "../fixtures/Graphene.json";
import H2HFinal_JSON from "../fixtures/H2+H-final.json";
import H2HImage_JSON from "../fixtures/H2+H-image.json";
import H2HInitial_JSON from "../fixtures/H2+H-initial.json";
import LiFeSiBasis_JSON from "../fixtures/LiFeSi-basis.json";
import LiFeSiBasisLabels_JSON from "../fixtures/LiFeSi-basis-labels.json";
import Na_JSON from "../fixtures/Na.json";
import Na4Cl4_JSON from "../fixtures/Na4Cl4.json";
import Na4Cl4Cartesian_JSON from "../fixtures/Na4Cl4-cartesian.json";
import NiHex_JSON from "../fixtures/Ni-hex.json";
import OSiBasis_JSON from "../fixtures/OSi-basis.json";
import SiSlab_JSON from "../fixtures/Si-slab.json";
import SiSlab100_JSON from "../fixtures/si-slab-100.json";
import SiSlab111Gamma120_JSON from "../fixtures/si-slab-111-0.5-vacuum-gamma-120.json";
import SiSlab111_JSON from "../fixtures/si-slab-111-0.5-vacuum-ratio.json";
import SiSlab111NoVacuum_JSON from "../fixtures/si-slab-111-0-vacuum.json";
import Silicon_JSON from "../fixtures/si-standata.json";

import SiSupercell_JSON from "../fixtures/Si-supercell.json";
import Si2Basis_JSON from "../fixtures/Si2-basis.json";
import Si2BasisRepeated_JSON from "../fixtures/Si2-basis-repeated.json";
import Zr1H23Zr1H1_JSON from "../fixtures/Zr1H23Zr1H1.json";

// Material
const Silicon = Silicon_JSON as unknown as MaterialSchema;
const SiSupercell = SiSupercell_JSON as unknown as MaterialSchema;
const SiSlab = SiSlab_JSON as unknown as MaterialSchema;
const SiSlab100 = SiSlab100_JSON as unknown as MaterialSchema;
const SiSlab111 = SiSlab111_JSON as unknown as MaterialSchema;
const SiSlab111Gamma120 = SiSlab111Gamma120_JSON as unknown as MaterialSchema;
const SiSlab111NoVacuum = SiSlab111NoVacuum_JSON as unknown as MaterialSchema;
const FeO = FeO_JSON as unknown as MaterialSchema;
const FeOStandata = MaterialStandata.getRuntimeDataConfigs().find(
    (m: any) => m.name?.includes("FeO"),
) as MaterialSchema;
const Na4Cl4 = Na4Cl4_JSON as unknown as MaterialSchema;
const Na4Cl4Cartesian = Na4Cl4Cartesian_JSON as unknown as MaterialSchema;
const C2H4 = C2H4_JSON as unknown as MaterialSchema;
const C2H4Translated = C2H4Translated_JSON as unknown as MaterialSchema;
const Na = Na_JSON as unknown as MaterialSchema;
const H2HInitial = H2HInitial_JSON as unknown as MaterialSchema;
const H2HFinal = H2HFinal_JSON as unknown as MaterialSchema;
const H2HImage = H2HImage_JSON as unknown as MaterialSchema;
const Zr1H23Zr1H1 = Zr1H23Zr1H1_JSON as unknown as MaterialSchema;
const Graphene = Graphene_JSON as unknown as MaterialSchema;
const NiHex = NiHex_JSON as unknown as MaterialSchema;

// Basis
const Si2Basis = Si2Basis_JSON as BasisSchema;
const Si2BasisRepeated = Si2BasisRepeated_JSON as BasisSchema;
const OSiBasis = OSiBasis_JSON as BasisSchema;
const Ge2Basis = Ge2Basis_JSON as BasisSchema;
const AsGeBasis = AsGeBasis_JSON as BasisSchema;
const FeLiSiBasis = FeLiSiBasis_JSON as BasisSchema;
const LiFeSiBasis = LiFeSiBasis_JSON as BasisSchema;
const LiFeSiBasisLabels = LiFeSiBasisLabels_JSON as BasisSchema;

// Other
const atomicConstraints = atomicConstraints_JSON as AtomicConstraintsSchema;

export {
    // Silicon
    Silicon,
    SiSupercell,
    SiSlab,
    SiSlab100,
    SiSlab111,
    SiSlab111Gamma120,
    SiSlab111NoVacuum,
    Si2Basis,
    Si2BasisRepeated,
    // Other
    FeO,
    FeOStandata,
    Na4Cl4,
    Na4Cl4Cartesian,
    C2H4,
    C2H4Translated,
    Na,
    OSiBasis,
    Ge2Basis,
    AsGeBasis,
    FeLiSiBasis,
    LiFeSiBasis,
    LiFeSiBasisLabels,
    atomicConstraints,
    H2HInitial,
    H2HFinal,
    H2HImage,
    Zr1H23Zr1H1,
    Graphene,
    NiHex,
};

// NON-JSON
export const FIXTURES_DIR = path.resolve(__dirname, "../fixtures");

// NON-JSON
export const Na4Cl4Poscar = fs.readFileSync(path.join(FIXTURES_DIR, "Na4Cl4.poscar"), "utf8");
export const SiPWSCFInput = fs.readFileSync(path.join(FIXTURES_DIR, "Si-pwscf.in"), "utf8");
export const Zr1H23Zr1H1Poscar = fs.readFileSync(
    path.join(FIXTURES_DIR, "Zr1H23Zr1H1.poscar"),
    "utf8",
);
export const H2OPoscar = fs.readFileSync(path.join(FIXTURES_DIR, "H2O.poscar"), "utf8");
export const GraphenePoscar = fs.readFileSync(path.join(FIXTURES_DIR, "Graphene.poscar"), "utf8");
export const NiHexPoscar = fs.readFileSync(path.join(FIXTURES_DIR, "Ni-hex.poscar"), "utf8");
