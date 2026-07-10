"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.symmetryPoints = symmetryPoints;
const POINTS = {
    CUB: () => {
        return [
            {
                point: "R",
                coordinates: [0.5, 0.5, 0.5],
            },
            {
                point: "X",
                coordinates: [0.0, 0.5, 0.0],
            },
            {
                point: "M",
                coordinates: [0.5, 0.5, 0.0],
            },
        ];
    },
    FCC: () => {
        return [
            {
                point: "K",
                coordinates: [3 / 8, 3 / 8, 3 / 4],
            },
            {
                point: "L",
                coordinates: [1 / 2, 1 / 2, 1 / 2],
            },
            {
                point: "U",
                coordinates: [5 / 8, 1 / 4, 5 / 8],
            },
            {
                point: "W",
                coordinates: [1 / 2, 1 / 4, 3 / 4],
            },
            {
                point: "X",
                coordinates: [1 / 2, 0.0, 1 / 2],
            },
        ];
    },
    BCC: () => {
        return [
            {
                point: "H",
                coordinates: [1 / 2, -1 / 2, 1 / 2],
            },
            {
                point: "P",
                coordinates: [1 / 4, 1 / 4, 1 / 4],
            },
            {
                point: "N",
                coordinates: [0.0, 0.0, 1 / 2],
            },
        ];
    },
    TET: () => {
        return [
            {
                point: "A",
                coordinates: [1 / 2, 1 / 2, 1 / 2],
            },
            {
                point: "M",
                coordinates: [1 / 2, 1 / 2, 0.0],
            },
            {
                point: "R",
                coordinates: [0.0, 1 / 2, 1 / 2],
            },
            {
                point: "X",
                coordinates: [0.0, 1 / 2, 0.0],
            },
            {
                point: "Z",
                coordinates: [0.0, 0.0, 1 / 2],
            },
        ];
    },
    BCT: ({ a, c }) => {
        let n;
        if (c < a) {
            // BCT-1
            n = (1 + (c * c) / (a * a)) / 4;
            return [
                {
                    point: "M",
                    coordinates: [-1 / 2, 1 / 2, 1 / 2],
                },
                {
                    point: "N",
                    coordinates: [0.0, 1 / 2, 0.0],
                },
                {
                    point: "P",
                    coordinates: [1 / 4, 1 / 4, 1 / 4],
                },
                {
                    point: "X",
                    coordinates: [0.0, 0.0, 1 / 2],
                },
                {
                    point: "Z",
                    coordinates: [n, n, -n],
                },
                {
                    point: "Z1",
                    coordinates: [-n, 1 - n, n],
                },
            ];
        }
        // BCT-2
        n = (1 + (a * a) / (c * c)) / 4;
        const e = (a * a) / (2 * c * c);
        return [
            {
                point: "N",
                coordinates: [0.0, 1 / 2, 0.0],
            },
            {
                point: "P",
                coordinates: [1 / 4, 1 / 4, 1 / 4],
            },
            {
                point: "∑",
                coordinates: [-n, n, n],
            },
            {
                point: "∑1",
                coordinates: [n, 1 - n, -n],
            },
            {
                point: "X",
                coordinates: [0, 0, 1 / 2],
            },
            {
                point: "Y",
                coordinates: [-e, e, 1 / 2],
            },
            {
                point: "Y1",
                coordinates: [1 / 2, 1 / 2, -e],
            },
            {
                point: "Z",
                coordinates: [1 / 2, 1 / 2, -1 / 2],
            },
        ];
    },
    ORC: () => {
        return [
            {
                point: "R",
                coordinates: [1 / 2, 1 / 2, 1 / 2],
            },
            {
                point: "S",
                coordinates: [1 / 2, 1 / 2, 0.0],
            },
            {
                point: "T",
                coordinates: [0.0, 1 / 2, 1 / 2],
            },
            {
                point: "U",
                coordinates: [1 / 2, 0.0, 1 / 2],
            },
            {
                point: "X",
                coordinates: [1 / 2, 0.0, 0.0],
            },
            {
                point: "Y",
                coordinates: [0.0, 1 / 2, 0.0],
            },
            {
                point: "Z",
                coordinates: [0.0, 0.0, 1 / 2],
            },
        ];
    },
    ORCF: ({ a, b, c }) => {
        let n;
        if (1 / (a * a) >= 1 / (b * b) + 1 / (c * c)) {
            // ORCF-1,3
            n = (1 + (a * a) / (b * b) + (a * a) / (c * c)) / 4;
            const e = (1 + (a * a) / (b * b) - (a * a) / (c * c)) / 4;
            return [
                {
                    point: "A",
                    coordinates: [1 / 2, 1 / 2 + e, e],
                },
                {
                    point: "A1",
                    coordinates: [0.0, 1 / 2 - e, 1 - e],
                },
                {
                    point: "L",
                    coordinates: [1 / 2, 1 / 2, 1 / 2],
                },
                {
                    point: "T",
                    coordinates: [1.0, 1 / 2, 1 / 2],
                },
                {
                    point: "X",
                    coordinates: [0.0, n, n],
                },
                {
                    point: "X1",
                    coordinates: [1.0, 1 - n, 1 - n],
                },
                {
                    point: "Y",
                    coordinates: [1 / 2, 0.0, 1 / 2],
                },
                {
                    point: "Z",
                    coordinates: [1 / 2, 1 / 2, 0.0],
                },
            ];
        }
        // ORCF-2
        n = (1 + (a * a) / (b * b) - (a * a) / (c * c)) / 4;
        const f = (1 + (c * c) / (b * b) - (c * c) / (a * a)) / 4;
        const d = (1 + (b * b) / (a * a) - (b * b) / (c * c)) / 4;
        return [
            {
                point: "C",
                coordinates: [1 / 2, 1 / 2 - n, 1 - n],
            },
            {
                point: "C1",
                coordinates: [0.0, 1 / 2 + n, n],
            },
            {
                point: "D",
                coordinates: [1 / 2 - d, 1 / 2, 1 - d],
            },
            {
                point: "D1",
                coordinates: [1 / 2 + d, 1 / 2, d],
            },
            {
                point: "L",
                coordinates: [1 / 2, 1 / 2, 1 / 2],
            },
            {
                point: "H",
                coordinates: [1 - f, 1 / 2 - f, 1 / 2],
            },
            {
                point: "H1",
                coordinates: [f, 1 / 2 + f, 1 / 2],
            },
            {
                point: "X",
                coordinates: [0.0, 1 / 2, 1 / 2],
            },
            {
                point: "Y",
                coordinates: [1 / 2, 0.0, 1 / 2],
            },
            {
                point: "Z",
                coordinates: [1 / 2, 1 / 2, 0.0],
            },
        ];
    },
    ORCI: ({ a, b, c }) => {
        const n = (1 + (a * a) / (c * c)) / 4;
        const e = (1 + (b * b) / (c * c)) / 4;
        const d = (b * b - a * a) / (4 * c * c);
        const m = (b * b + a * a) / (4 * c * c);
        return [
            {
                point: "L",
                coordinates: [-m, m, 1 / 2 - d],
            },
            {
                point: "L1",
                coordinates: [m, -m, 1 / 2 + d],
            },
            {
                point: "L2",
                coordinates: [1 / 2 - d, 1 / 2 + d, -m],
            },
            {
                point: "R",
                coordinates: [0.0, 1 / 2, 0.0],
            },
            {
                point: "S",
                coordinates: [1 / 2, 0.0, 0.0],
            },
            {
                point: "T",
                coordinates: [0.0, 0.0, 1 / 2],
            },
            {
                point: "W",
                coordinates: [1 / 4, 1 / 4, 1 / 4],
            },
            {
                point: "X",
                coordinates: [-e, e, e],
            },
            {
                point: "X1",
                coordinates: [e, 1 - e, -e],
            },
            {
                point: "Y",
                coordinates: [n, -n, n],
            },
            {
                point: "Y1",
                coordinates: [1 - n, n, -n],
            },
            {
                point: "Z",
                coordinates: [1 / 2, 1 / 2, -1 / 2],
            },
        ];
    },
    ORCC: ({ a, b }) => {
        const e = (1 + (a * a) / (b * b)) / 4;
        return [
            {
                point: "A",
                coordinates: [e, e, 1 / 2],
            },
            {
                point: "A1",
                coordinates: [-e, 1 - e, 1 / 2],
            },
            {
                point: "R",
                coordinates: [0.0, 1 / 2, 1 / 2],
            },
            {
                point: "S",
                coordinates: [0.0, 1 / 2, 0.0],
            },
            {
                point: "T",
                coordinates: [-1 / 2, 1 / 2, 1 / 2],
            },
            {
                point: "X",
                coordinates: [e, e, 0.0],
            },
            {
                point: "X1",
                coordinates: [-e, 1 - e, 0.0],
            },
            {
                point: "Y",
                coordinates: [-1 / 2, 1 / 2, 0.0],
            },
            {
                point: "Z",
                coordinates: [0.0, 0.0, 1 / 2],
            },
        ];
    },
    HEX: () => {
        return [
            {
                point: "A",
                coordinates: [0.0, 0.0, 1 / 2],
            },
            {
                point: "H",
                coordinates: [1 / 3, 1 / 3, 1 / 2],
            },
            {
                point: "K",
                coordinates: [1 / 3, 1 / 3, 0.0],
            },
            {
                point: "L",
                coordinates: [1 / 2, 0.0, 1 / 2],
            },
            {
                point: "M",
                coordinates: [1 / 2, 0.0, 0.0],
            },
        ];
    },
    RHL: ({ alpha }) => {
        let n, v;
        const cosAlpha = Math.cos((alpha / 180) * Math.PI);
        if (cosAlpha > 0) {
            // RHL-1
            n = (1 + 4 * cosAlpha) / (2 + 4 * cosAlpha);
            v = 3 / 4 - n / 2;
            return [
                {
                    point: "B",
                    coordinates: [n, 1 / 2, 1 - n],
                },
                {
                    point: "B1",
                    coordinates: [1 / 2, 1 - n, n - 1],
                },
                {
                    point: "F",
                    coordinates: [1 / 2, 1 / 2, 0.0],
                },
                {
                    point: "L",
                    coordinates: [1 / 2, 0.0, 0.0],
                },
                {
                    point: "L1",
                    coordinates: [0.0, 0.0, -1 / 2],
                },
                {
                    point: "P",
                    coordinates: [n, v, v],
                },
                {
                    point: "P1",
                    coordinates: [1 - v, 1 - v, 1 - n],
                },
                {
                    point: "P2",
                    coordinates: [v, v, n - 1],
                },
                {
                    point: "Q",
                    coordinates: [1 - v, v, 0.0],
                },
                {
                    point: "X",
                    coordinates: [v, 0.0, -v],
                },
                {
                    point: "Z",
                    coordinates: [1 / 2, 1 / 2, 1 / 2],
                },
            ];
        }
        // RHL-2
        n = ((1 / 2) * (1 + cosAlpha)) / (1 - cosAlpha);
        v = 3 / 4 - n / 2;
        return [
            {
                point: "F",
                coordinates: [1 / 2, -1 / 2, 0.0],
            },
            {
                point: "L",
                coordinates: [1 / 2, 0.0, 0.0],
            },
            {
                point: "P",
                coordinates: [1 - v, -v, 1 - v],
            },
            {
                point: "P1",
                coordinates: [v, v - 1, v - 1],
            },
            {
                point: "Q",
                coordinates: [n, n, n],
            },
            {
                point: "Q1",
                coordinates: [1 - n, -n, -n],
            },
            {
                point: "Z",
                coordinates: [1 / 2, -1 / 2, 1 / 2],
            },
        ];
    },
    MCL: ({ b, c, alpha }) => {
        const cosAlpha = Math.cos((alpha / 180) * Math.PI);
        const n = ((1 / 2) * (1 - (b * cosAlpha) / c)) / (1 - cosAlpha * cosAlpha);
        const v = 1 / 2 - (n * c * cosAlpha) / b;
        return [
            {
                point: "A",
                coordinates: [1 / 2, 1 / 2, 0.0],
            },
            {
                point: "C",
                coordinates: [0.0, 1 / 2, 1 / 2],
            },
            {
                point: "D",
                coordinates: [1 / 2, 0.0, 1 / 2],
            },
            {
                point: "D1",
                coordinates: [1 / 2, 0.0, -1 / 2],
            },
            {
                point: "E",
                coordinates: [1 / 2, 1 / 2, 1 / 2],
            },
            {
                point: "H",
                coordinates: [0.0, n, 1 - v],
            },
            {
                point: "H1",
                coordinates: [0.0, 1 - n, v],
            },
            {
                point: "H2",
                coordinates: [0.0, n, -v],
            },
            {
                point: "M",
                coordinates: [1 / 2, n, 1 - v],
            },
            {
                point: "M1",
                coordinates: [1 / 2, 1 - n, v],
            },
            {
                point: "M2",
                coordinates: [1 / 2, n, -v],
            },
            {
                point: "X",
                coordinates: [0.0, 1 / 2, 0.0],
            },
            {
                point: "Y",
                coordinates: [0.0, 0.0, 1 / 2],
            },
            {
                point: "Y1",
                coordinates: [0.0, 0.0, -1 / 2],
            },
            {
                point: "Z",
                coordinates: [1 / 2, 0.0, 0.0],
            },
        ];
    },
    MCLC: ({ a, b, c, alpha, gamma }) => {
        const cosAlpha = Math.cos((alpha / 180) * Math.PI);
        let e, n, p, f, m, d, v;
        if (gamma >= 90) {
            // MCLC-1,2
            e = (2 - (b * cosAlpha) / c) / (4 * (1 - cosAlpha * cosAlpha));
            n = 1 / 2 + (2 * e * c * cosAlpha) / b;
            p = 3 / 4 - (a * a) / (4 * b * b * (1 - cosAlpha * cosAlpha));
            f = p + ((3 / 4 - p) * cosAlpha * b) / c;
            return [
                {
                    point: "N",
                    coordinates: [1 / 2, 0.0, 0.0],
                },
                {
                    point: "N1",
                    coordinates: [0.0, -1 / 2, 0.0],
                },
                {
                    point: "F",
                    coordinates: [1 - e, 1 - e, 1 - n],
                },
                {
                    point: "F1",
                    coordinates: [e, e, n],
                },
                {
                    point: "F2",
                    coordinates: [-e, -e, 1 - n],
                },
                {
                    point: "F3",
                    coordinates: [1 - e, -e, 1 - n],
                },
                {
                    point: "I",
                    coordinates: [f, 1 - f, 1 / 2],
                },
                {
                    point: "I1",
                    coordinates: [1 - f, f - 1, 1 / 2],
                },
                {
                    point: "L",
                    coordinates: [1 / 2, 1 / 2, 1 / 2],
                },
                {
                    point: "M",
                    coordinates: [1 / 2, 0.0, 1 / 2],
                },
                {
                    point: "X",
                    coordinates: [1 - p, p - 1, 0.0],
                },
                {
                    point: "X1",
                    coordinates: [p, 1 - p, 0.0],
                },
                {
                    point: "X2",
                    coordinates: [p - 1, -p, 0.0],
                },
                {
                    point: "Y",
                    coordinates: [1 / 2, 1 / 2, 0.0],
                },
                {
                    point: "Y1",
                    coordinates: [-1 / 2, -1 / 2, 0.0],
                },
                {
                    point: "Z",
                    coordinates: [0.0, 0.0, 1 / 2],
                },
            ];
        }
        if ((b / c) * cosAlpha + ((b * b) / (a * a)) * (1 - cosAlpha * cosAlpha) <= 1) {
            // MCLC-3,4
            m = (1 + (b * b) / (a * a)) / 4;
            d = (b * c * cosAlpha) / (2 * a * a);
            e = m - 1 / 4 + (1 - (b * cosAlpha) / c) / (4 * (1 - cosAlpha * cosAlpha));
            n = 1 / 2 + (2 * e * c * cosAlpha) / b;
            f = 1 + e - 2 * m;
            p = n - 2 * d;
            return [
                {
                    point: "N",
                    coordinates: [1 / 2, 0.0, 0.0],
                },
                {
                    point: "N1",
                    coordinates: [0.0, -1 / 2, 0.0],
                },
                {
                    point: "F",
                    coordinates: [1 - f, 1 - f, 1 - p],
                },
                {
                    point: "F1",
                    coordinates: [f, f - 1, p],
                },
                {
                    point: "F2",
                    coordinates: [1 - f, -f, 1 - p],
                },
                {
                    point: "H",
                    coordinates: [e, e, n],
                },
                {
                    point: "H1",
                    coordinates: [1 - e, -e, 1 - n],
                },
                {
                    point: "H2",
                    coordinates: [-e, -e, 1 - n],
                },
                {
                    point: "I",
                    coordinates: [1 / 2, -1 / 2, 1 / 2],
                },
                {
                    point: "M",
                    coordinates: [1 / 2, 0.0, 1 / 2],
                },
                {
                    point: "X",
                    coordinates: [1 / 2, -1 / 2, 0.0],
                },
                {
                    point: "Y",
                    coordinates: [m, m, d],
                },
                {
                    point: "Y1",
                    coordinates: [1 - m, -m, -d],
                },
                {
                    point: "Y2",
                    coordinates: [-m, -m, -d],
                },
                {
                    point: "Y3",
                    coordinates: [m, m - 1, d],
                },
                {
                    point: "Z",
                    coordinates: [0.0, 0.0, 1 / 2],
                },
            ];
        }
        // MCLC-5
        e = (1 / 4) * ((b * b) / (a * a) + (1 - (b * cosAlpha) / c) / (1 - cosAlpha * cosAlpha));
        // @ts-ignore
        m = n / 2 + (b * b) / (a * a) / 4 - (b * c * cosAlpha) / (2 * a * a);
        // eslint-disable-next-line max-len
        const w = // @ts-ignore
         ((4 * v - 1 - (b * b * (1 - cosAlpha * cosAlpha)) / (a * a)) * c) / (2 * b * cosAlpha);
        n = 1 / 2 + (2 * e * c * cosAlpha) / b;
        d = ((e * c) / b) * cosAlpha + w / 2 - 1 / 4;
        v = 1 + e - 2 * m;
        const r = 1 - (e * a * a) / (b * b);
        return [
            {
                point: "N",
                coordinates: [1 / 2, 0.0, 0.0],
            },
            {
                point: "N1",
                coordinates: [0.0, -1 / 2, 0.0],
            },
            {
                point: "F",
                coordinates: [v, v, w],
            },
            {
                point: "F1",
                coordinates: [1 - v, 1 - v, 1 - w],
            },
            {
                point: "F2",
                coordinates: [v, v - 1, w],
            },
            {
                point: "H",
                coordinates: [e, e, n],
            },
            {
                point: "H1",
                coordinates: [1 - e, -e, 1 - n],
            },
            {
                point: "H2",
                coordinates: [-e, -e, 1 - n],
            },
            {
                point: "I",
                coordinates: [r, 1 - r, 1 / 2],
            },
            {
                point: "I1",
                coordinates: [1 - r, r - 1, 1 / 2],
            },
            {
                point: "L",
                coordinates: [1 / 2, 1 / 2, 1 / 2],
            },
            {
                point: "M",
                coordinates: [1 / 2, 0.0, 1 / 2],
            },
            {
                point: "X",
                coordinates: [1 / 2, -1 / 2, 0.0],
            },
            {
                point: "Y",
                coordinates: [m, m, d],
            },
            {
                point: "Y1",
                coordinates: [1 - m, -m, -d],
            },
            {
                point: "Y2",
                coordinates: [-m, -m, -d],
            },
            {
                point: "Y3",
                coordinates: [m, m - 1, d],
            },
            {
                point: "Z",
                coordinates: [0.0, 0.0, 1 / 2],
            },
        ];
    },
    TRI: ({ alpha, beta, gamma }) => {
        if (alpha > 90 && beta > 90 && gamma >= 90) {
            // TRI-1a,2a
            return [
                {
                    point: "L",
                    coordinates: [1 / 2, 1 / 2, 0.0],
                },
                {
                    point: "M",
                    coordinates: [0.0, 1 / 2, 1 / 2],
                },
                {
                    point: "N",
                    coordinates: [1 / 2, 0.0, 1 / 2],
                },
                {
                    point: "R",
                    coordinates: [1 / 2, 1 / 2, 1 / 2],
                },
                {
                    point: "X",
                    coordinates: [1 / 2, 0.0, 0.0],
                },
                {
                    point: "Y",
                    coordinates: [0.0, 1 / 2, 0.0],
                },
                {
                    point: "Z",
                    coordinates: [0.0, 0.0, 1 / 2],
                },
            ];
        }
        // TRI-1b,2b
        return [
            {
                point: "L",
                coordinates: [1 / 2, -1 / 2, 0.0],
            },
            {
                point: "M",
                coordinates: [0.0, 0.0, 1 / 2],
            },
            {
                point: "N",
                coordinates: [-1 / 2, -1 / 2, 1 / 2],
            },
            {
                point: "R",
                coordinates: [0.0, -1 / 2, 1 / 2],
            },
            {
                point: "X",
                coordinates: [0.0, -1 / 2, 0.0],
            },
            {
                point: "Y",
                coordinates: [1 / 2, 0.0, 0.0],
            },
            {
                point: "Z",
                coordinates: [-1 / 2, 0.0, 1 / 2],
            },
        ];
    },
};
/**
 * Returns a list of symmetry points for the specified lattice.
 */
function symmetryPoints(lattice) {
    return [
        {
            point: "Г",
            coordinates: [0.0, 0.0, 0.0],
        },
    ].concat(POINTS[lattice.type](lattice) || []);
}
