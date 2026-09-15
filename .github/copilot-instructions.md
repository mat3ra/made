# Copilot Instructions for Made

## Repository Overview

Made is a library for **MA**terials **DE**sign that enables creating and manipulating material structures from atoms up. The library is designed for web applications, supporting both client (web browser) and server (Node.js) environments, with implementations in both JavaScript/TypeScript and Python (including Pyodide).

## Key Concepts

- **Dual Language Support**: This repository contains both JavaScript/TypeScript (`src/js/`) and Python (`src/py/`) implementations
- **ESSE Data Convention**: All classes follow the Exabyte Source of Schemas and Examples (ESSE) data structures
- **Materials-Only Focus**: Code should only handle materials-related functionality, not simulation model parameters

## Code Structure

### Directory Organization

- `src/js/` - JavaScript/TypeScript implementation
  - `basis/` - Basis representation and operations
  - `lattice/` - Lattice structures and reciprocal lattice
  - `cell/` - Unit cell operations
  - `constraints/` - Atomic constraints
  - `parsers/` - File format parsers (POSCAR, XYZ, Quantum ESPRESSO, etc.)
  - `tools/` - Helper functions that act on classes with external parameters
- `src/py/` - Python implementation
  - `mat3ra/made/` - Main Python package
  - `mat3ra/made/tools/` - Python tools with optional dependencies
- `tests/js/` - JavaScript/TypeScript tests
- `tests/py/` - Python tests

### Key Classes

- `Material` - High-level material representation
- `Basis` - Atomic positions and elements
- `Lattice` - Crystal lattice structure
- `ReciprocalLattice` - Reciprocal space representation
- `Cell` - Unit cell geometry
- `AtomicConstraints` - Constraints on atomic positions

## Development Guidelines

### General Conventions

1. **Object-Oriented Design**: Use classes following ESSE data structures
2. **Tools Pattern**: Functions requiring external parameters belong in `tools/`, not as class methods
   - Example: `basis.clone()` is a method, but basis repetition is in `tools/basis.js` because it requires external repetition parameters
3. **Minimal Modifications**: Make the smallest possible changes to address issues
4. **No Simulation Parameters**: Keep simulation model parameters (approximations, numerical parameters) out of this library

### JavaScript/TypeScript

- **Language**: TypeScript with ES6+ features
- **Testing**: Mocha framework with Chai assertions
- **Linting**: ESLint with Prettier formatting
- **Code Style**: 
  - Use existing libraries when possible
  - Avoid adding new dependencies unless necessary
  - Match existing comment style in files
  
#### Running Tests

```bash
npm install
npm test
```

#### Linting

```bash
npm run lint        # Check and format
npm run lint:fix    # Auto-fix issues
```

**Note**: Pre-commit hooks automatically run linters. Staged files may be modified during commit to fix style issues.

### Python

- **Version**: Python 3.8+ required
- **Testing**: PyTest framework
- **Tools Module**: Has optional dependencies on `pymatgen` and `ase`
  - Prefer ASE over pymatgen for new functionality
  - Mark as optional to avoid forcing users to install heavy dependencies

#### Running Tests

```bash
virtualenv .venv
source .venv/bin/activate
pip install ".[tests]"
pytest tests/py
```

#### Development for Pyodide

```bash
wheel_server  # Build and serve locally
```

## Testing Guidelines

### JavaScript/TypeScript

1. Mirror directory structure: Each module in `src/js/` should have a corresponding test in `tests/js/`
2. Use fixtures: Place test data in `tests/fixtures/` (automatically stored in Git LFS)
3. Share fixtures: Export common fixtures in `tests/enums.js` to avoid duplication
4. Setup hooks: Use `tests/setup.js` for test environment preparation

### Python

- Write PyTest-compatible tests in `tests/py/`
- Keep test structure parallel to source structure

## File Format Support

The library supports various materials file formats:
- **POSCAR** - VASP crystal structure format
- **XYZ** - Simple atomic coordinates format
- **Quantum ESPRESSO** - QE input/output formats
- **CIF** - Crystallographic Information File (partial support)

## Git LFS

Test fixtures are stored using Git LFS. After cloning:

```bash
git lfs pull
```

## Common Tasks

### Adding a New Material Property

1. Add to appropriate class in both `src/js/` and `src/py/`
2. Follow ESSE data convention
3. Add tests in both language implementations
4. Update relevant parsers if needed

### Adding a New Tool

1. Create in `tools/` directory (not as a class method)
2. Tools take class instances plus external parameters
3. Add comprehensive tests
4. Document parameters and behavior

### Updating Dependencies

- **JavaScript**: Update `package.json` carefully, check for security issues
- **Python**: Update `pyproject.toml`, keep optional dependencies separate

## Known Issues

### JavaScript/TypeScript
- Linter may auto-fix staged files during commit, causing confusion about what's committed

### Python
- Python 3.8 tests fail on Apple Silicon due to pymatgen issue #3521

## Important Notes

- **Never break existing tests** unless fixing them is the explicit goal
- **Match existing style** - don't add comments unless they match file style
- **Keep changes minimal** - surgical, precise modifications only
- **Test early and often** - validate changes incrementally
- **No new linting/testing tools** unless required to fix the issue
