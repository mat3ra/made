#!/usr/bin/env node

/**
 * Script to generate mixin properties from JSON schema.
 *
 * Usage:
 *   npm run generate-mixins
 */

import generateSchemaMixin from "@mat3ra/code/dist/js/generateSchemaMixin";
import allSchemas from "@mat3ra/esse/dist/js/schemas.json";
import type { JSONSchema7 } from "json-schema";

const SKIP_FIELDS: string[] = [];

const OUTPUT_PATHS = {
    "material/material-properties": "src/js/generated/MaterialSchemaMixin.ts",
};

function main() {
    const result = generateSchemaMixin(allSchemas as JSONSchema7[], OUTPUT_PATHS, SKIP_FIELDS);

    if (result.errorCount > 0) {
        process.exit(1);
    }
}

main();
