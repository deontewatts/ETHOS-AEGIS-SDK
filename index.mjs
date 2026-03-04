/**
 * @ethos-aegis/sdk — ESM entry point
 * Re-exports from the CJS module for full ESM compatibility.
 */
import { createRequire } from "module";
const require = createRequire(import.meta.url);
const sdk = require("./index.js");

export const { AegisClient, AegisError, AegisTransportError, adjudicate, assertSanctified } = sdk;
export default sdk;
