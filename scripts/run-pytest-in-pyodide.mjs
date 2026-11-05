// Runs pytest in Pyodide 0.24.1, the JupyterLite runtime, with the packages the made notebooks install there.
// Usage: node run-pytest-in-pyodide.mjs <made checkout> <made wheel directory> <pytest arguments...>
import { createRequire } from "module";

// The CommonJS build: pyodide 0.24's ES module resolves its files against the working directory under Node.
const { loadPyodide } = createRequire(import.meta.url)("pyodide");

const [checkoutDirectory, wheelDirectory, ...pytestArguments] = process.argv.slice(2);

// api-examples config.yml, notebook "made", installed in order as JupyterLite does: wheels without dependencies.
const WHEELS_URL =
    "https://media.githubusercontent.com/media/mat3ra/api-examples/531be320c6597b24811e6935cc0a7f09646f4707/packages";
const PACKAGES = [
    "annotated_types>=0.6.0",
    "networkx==3.2.1",
    "monty==2023.11.3",
    "scipy==1.11.2",
    "tabulate==0.9.0",
    "sympy==1.12",
    "uncertainties==3.1.6",
    "ase==3.25.0",
    `${WHEELS_URL}/pymatgen-2024.4.13-py3-none-any.whl`,
    `${WHEELS_URL}/spglib-2.0.2-py3-none-any.whl`,
    `${WHEELS_URL}/ruamel.yaml-0.17.32-py3-none-any.whl`,
    `${WHEELS_URL}/pydantic_core-2.18.2-py3-none-any.whl`,
    `${WHEELS_URL}/pydantic-2.7.1-py3-none-any.whl`,
    "mp-pyrho==0.5.1",
    "pymatgen-analysis-defects<=2024.4.23",
    "mat3ra-periodic-table",
    "mat3ra-code",
    "mat3ra-esse",
    "mat3ra-utils",
    "mat3ra-standata",
    `emfs:${wheelDirectory}/mat3ra_made-0.0.0-py3-none-any.whl`,
];

const pyodide = await loadPyodide();
for (const directory of [checkoutDirectory, wheelDirectory]) {
    pyodide.FS.mkdirTree(directory);
    pyodide.FS.mount(pyodide.FS.filesystems.NODEFS, { root: directory }, directory);
}
await pyodide.loadPackage(["micropip", "pytest", "lzma", "sqlite3", "typing-extensions"]);
const micropip = pyodide.pyimport("micropip");
for (const name of PACKAGES) {
    await micropip.install.callKwargs(name, { deps: !name.endsWith(".whl") });
}
pyodide.FS.chdir(checkoutDirectory);
// made from its wheel, as JupyterLite installs it, not from src/py
pyodide.globals.set("arguments", pyodide.toPy(["-p", "no:cacheprovider", "-o", "pythonpath=", ...pytestArguments]));
process.exit(pyodide.runPython("import pytest; int(pytest.main(arguments))"));
