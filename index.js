/**
 * @ethos-aegis/sdk — Node.js / TypeScript SDK
 *
 * Three transport modes:
 *   1. subprocess  — calls Python core directly via child_process (default, zero infra)
 *   2. http        — calls a running Aegis REST server (production recommended)
 *   3. embedded    — reserved for future N-API / WASM binding
 *
 * Usage (ESM):
 *   import { AegisClient } from "@ethos-aegis/sdk";
 *   const client = new AegisClient();
 *   const result = await client.adjudicate("user payload");
 *
 * Usage (CJS):
 *   const { AegisClient } = require("@ethos-aegis/sdk");
 */

"use strict";

const { execFileSync, execFile } = require("child_process");
const path   = require("path");
const https  = require("https");
const http   = require("http");
const crypto = require("crypto");

// ── Repo root resolution ──────────────────────────────────────────────────────
const REPO_ROOT = path.resolve(__dirname, "..", "..", "..");

// ══════════════════════════════════════════════════════════════════════════════
// TYPES (JSDoc — consumed by TypeScript via @ts-check / d.ts generation)
// ══════════════════════════════════════════════════════════════════════════════

/**
 * @typedef {"VOID"|"TRACE"|"CAUTION"|"GRAVE"|"CONDEMNED"} DepthLabel
 */

/**
 * @typedef {Object} AegisVerdict
 * @property {boolean}    sanctified   - Payload cleared all stages
 * @property {boolean}    condemned    - Payload triggered terminal rule
 * @property {DepthLabel} depth        - Highest corruption depth found
 * @property {number}     malignaCount - Total threats detected
 * @property {boolean}    sanitized    - Payload was cleaned before forwarding
 * @property {string}     report       - Full axiological report text
 * @property {number}     latencyMs    - Pipeline latency in milliseconds
 * @property {string}     requestId    - Unique ID for this adjudication
 */

/**
 * @typedef {Object} AegisClientOptions
 * @property {"subprocess"|"http"}  [transport="subprocess"] - Transport backend
 * @property {string}  [pythonBin="python3"]  - Python executable (subprocess mode)
 * @property {string}  [repoRoot]             - Path to Ethos Aegis repo root
 * @property {string}  [serverUrl]            - Aegis REST server URL (http mode)
 * @property {string}  [apiKey]               - Bearer token for REST server
 * @property {number}  [timeoutMs=15000]      - Request timeout
 * @property {boolean} [throwOnCondemned=false] - Throw AegisError if condemned
 * @property {boolean} [verbose=false]
 */

/**
 * @typedef {Object} GuardedCallOptions
 * @property {Function} llmFn   - Async function (message:string) => string
 * @property {string}   message - User message to adjudicate then forward
 * @property {string}   [refusalMessage] - Override default refusal text
 */

// ══════════════════════════════════════════════════════════════════════════════
// ERRORS
// ══════════════════════════════════════════════════════════════════════════════

class AegisError extends Error {
  /**
   * @param {string}     message
   * @param {AegisVerdict} verdict
   */
  constructor(message, verdict) {
    super(message);
    this.name    = "AegisError";
    this.verdict = verdict;
  }
}

class AegisTransportError extends Error {
  constructor(message, cause) {
    super(message);
    this.name  = "AegisTransportError";
    this.cause = cause;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// SUBPROCESS TRANSPORT
// ══════════════════════════════════════════════════════════════════════════════

/** @param {string} payload @param {string} pythonBin @param {string} root @param {number} timeout */
function _subprocessAdjudicate(payload, pythonBin, root, timeout) {
  // Build a self-contained Python one-liner, passing payload via env var
  // to avoid any shell-quoting issues with special characters.
  const script = [
    "import sys, json, os",
    `sys.path.insert(0, ${JSON.stringify(root)})`,
    "from ethos_aegis import EthosAegis",
    "import time as _t",
    "a = EthosAegis()",
    "payload = os.environ['_AEGIS_PAYLOAD']",
    "t0 = _t.perf_counter()",
    "v = a.adjudicate(payload)",
    "ms = (_t.perf_counter() - t0) * 1000",
    "print(json.dumps({",
    "  'sanctified':   v.is_sanctified,",
    "  'condemned':    v.is_condemned,",
    "  'depth':        v.sovereignty_depth.name,",
    "  'malignaCount': len(v.maligna_found),",
    "  'sanitized':    v.purified_payload is not None,",
    "  'report':       v.axiological_report,",
    "  'latencyMs':    round(ms, 2),",
    "}))",
  ].join("\n");

  let raw;
  try {
    raw = execFileSync(pythonBin, ["-c", script], {
      encoding: "utf8",
      timeout,
      env: {
        ...process.env,
        _AEGIS_PAYLOAD: payload,
        AEGIS_LOG_LEVEL: "ERROR",   // suppress info logs in subprocess
      },
      maxBuffer: 5 * 1024 * 1024,
    });
  } catch (err) {
    throw new AegisTransportError(
      `Subprocess failed: ${err.message}`,
      err
    );
  }
  return JSON.parse(raw.trim());
}

// ══════════════════════════════════════════════════════════════════════════════
// HTTP TRANSPORT
// ══════════════════════════════════════════════════════════════════════════════

/** @param {string} url @param {Object} body @param {string} apiKey @param {number} timeout */
function _httpAdjudicate(url, body, apiKey, timeout) {
  return new Promise((resolve, reject) => {
    const data    = JSON.stringify(body);
    const parsed  = new URL(url);
    const lib     = parsed.protocol === "https:" ? https : http;
    const options = {
      hostname: parsed.hostname,
      port:     parsed.port || (parsed.protocol === "https:" ? 443 : 80),
      path:     parsed.pathname,
      method:   "POST",
      headers: {
        "Content-Type":   "application/json",
        "Content-Length": Buffer.byteLength(data),
        ...(apiKey ? { "Authorization": `Bearer ${apiKey}` } : {}),
      },
    };

    const req = lib.request(options, (res) => {
      let body = "";
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => {
        try {
          resolve(JSON.parse(body));
        } catch {
          reject(new AegisTransportError(`Invalid JSON from server: ${body.slice(0, 200)}`));
        }
      });
    });

    req.setTimeout(timeout, () => {
      req.destroy();
      reject(new AegisTransportError(`HTTP request timed out after ${timeout}ms`));
    });
    req.on("error", (e) =>
      reject(new AegisTransportError(`HTTP request failed: ${e.message}`, e))
    );
    req.write(data);
    req.end();
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// AEGIS CLIENT
// ══════════════════════════════════════════════════════════════════════════════

class AegisClient {
  /**
   * @param {AegisClientOptions} [options={}]
   */
  constructor(options = {}) {
    this._transport       = options.transport    || "subprocess";
    this._pythonBin       = options.pythonBin    || "python3";
    this._root            = options.repoRoot     || REPO_ROOT;
    this._serverUrl       = options.serverUrl    || "http://localhost:8080/v1/adjudicate";
    this._apiKey          = options.apiKey       || null;
    this._timeout         = options.timeoutMs    || 15_000;
    this._throwOnCondemned= options.throwOnCondemned || false;
    this._verbose         = options.verbose      || false;

    this._stats = { adjudications: 0, blocked: 0, sanitized: 0 };
  }

  // ── Core adjudication ─────────────────────────────────────────────────────

  /**
   * Adjudicate a payload through the full six-stage Ethos Aegis pipeline.
   * @param {string}  payload
   * @param {Object}  [context={}]
   * @returns {Promise<AegisVerdict>}
   */
  async adjudicate(payload, context = {}) {
    const requestId = crypto.randomBytes(8).toString("hex");
    let raw;

    if (this._transport === "subprocess") {
      // execFileSync is sync — wrap to keep API async-compatible
      raw = await Promise.resolve(
        _subprocessAdjudicate(payload, this._pythonBin, this._root, this._timeout)
      );
    } else if (this._transport === "http") {
      raw = await _httpAdjudicate(
        this._serverUrl,
        { payload, context, request_id: requestId },
        this._apiKey,
        this._timeout
      );
    } else {
      throw new AegisTransportError(`Unknown transport: ${this._transport}`);
    }

    /** @type {AegisVerdict} */
    const verdict = { ...raw, requestId };

    this._stats.adjudications++;
    if (verdict.condemned) this._stats.blocked++;
    if (verdict.sanitized) this._stats.sanitized++;

    if (this._verbose) {
      console.log(`[AegisClient] #${requestId} depth=${verdict.depth} sanctified=${verdict.sanctified} ${verdict.latencyMs}ms`);
    }

    if (this._throwOnCondemned && verdict.condemned) {
      throw new AegisError(
        `[EthosAegis] Payload CONDEMNED at depth ${verdict.depth}`,
        verdict
      );
    }

    return verdict;
  }

  /**
   * Guard an LLM call: adjudicate first, call the model only if safe.
   * @param {GuardedCallOptions} options
   * @returns {Promise<{ content: string, verdict: AegisVerdict, blocked: boolean }>}
   */
  async guard({ llmFn, message, refusalMessage }) {
    const refusal = refusalMessage ||
      "I'm not able to assist with that request.";

    const verdict = await this.adjudicate(message);
    if (verdict.condemned) {
      return { content: refusal, verdict, blocked: true };
    }
    const content = await llmFn(message);
    return { content, verdict, blocked: false };
  }

  /**
   * Adjudicate and throw if condemned. Useful as a middleware assert.
   * @param {string} payload
   * @returns {Promise<AegisVerdict>}
   * @throws {AegisError}
   */
  async assertSanctified(payload) {
    const verdict = await this.adjudicate(payload);
    if (verdict.condemned) {
      throw new AegisError(
        `Payload CONDEMNED at depth ${verdict.depth}`,
        verdict
      );
    }
    return verdict;
  }

  /**
   * Express / Fastify / Hono middleware factory.
   * Rejects condemned requests with HTTP 400 before they reach your route.
   *
   * @param {Object} [opts]
   * @param {string} [opts.field="message"] - Request body field to adjudicate
   * @returns {Function} Express-compatible middleware (req, res, next)
   *
   * @example
   * app.use(client.middleware());
   * // or adjudicate a specific field:
   * app.post("/chat", client.middleware({ field: "prompt" }), handler);
   */
  middleware(opts = {}) {
    const field = opts.field || "message";
    return async (req, res, next) => {
      const payload = (req.body && req.body[field]) || "";
      if (!payload) return next();
      try {
        const verdict = await this.adjudicate(payload);
        req.aegisVerdict = verdict;
        if (verdict.condemned) {
          return res.status(400).json({
            error: "Request blocked by Ethos Aegis.",
            depth: verdict.depth,
          });
        }
        next();
      } catch (err) {
        next(err);
      }
    };
  }

  // ── Stats ─────────────────────────────────────────────────────────────────

  stats() {
    return {
      ...this._stats,
      blockRate: this._stats.adjudications
        ? `${((this._stats.blocked / this._stats.adjudications) * 100).toFixed(1)}%`
        : "0%",
    };
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// CONVENIENCE FUNCTIONS
// ══════════════════════════════════════════════════════════════════════════════

/** Shared default client (lazy-initialized, subprocess transport) */
let _defaultClient = null;
function _getDefault() {
  if (!_defaultClient) _defaultClient = new AegisClient();
  return _defaultClient;
}

/**
 * Quick one-shot adjudication using the default subprocess client.
 * @param {string} payload
 * @returns {Promise<AegisVerdict>}
 */
async function adjudicate(payload) {
  return _getDefault().adjudicate(payload);
}

/**
 * Adjudicate and throw on CONDEMNED.
 * @param {string} payload
 * @returns {Promise<AegisVerdict>}
 */
async function assertSanctified(payload) {
  return _getDefault().assertSanctified(payload);
}

// ══════════════════════════════════════════════════════════════════════════════
// EXPORTS
// ══════════════════════════════════════════════════════════════════════════════

module.exports = {
  AegisClient,
  AegisError,
  AegisTransportError,
  adjudicate,
  assertSanctified,
};
