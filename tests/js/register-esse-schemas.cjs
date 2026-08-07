/**
 * Registers ESSE schemas for made unit tests.
 * Kept as CommonJS so mocha `--require` can load it without ESM JSON import issues.
 * Library / web-app code must not import `@mat3ra/esse/dist/js/schemas.json` — the host
 * (web-app) registers the (possibly extended) schema set once at startup.
 */
const JSONSchemasInterface = require("@mat3ra/esse/dist/js/esse/JSONSchemasInterface").default;
const allSchemas = require("@mat3ra/esse/dist/js/schemas.json");

JSONSchemasInterface.setSchemas(allSchemas);
