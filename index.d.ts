/**
 * Ethos Aegis — Node.js SDK TypeScript Definitions
 * Compatible with TypeScript ≥ 4.7, Node ≥ 18
 */

// ─── Core types ────────────────────────────────────────────────────────────

export type DepthLabel = "VOID" | "TRACE" | "CAUTION" | "GRAVE" | "CONDEMNED";
export type TransportMode = "subprocess" | "http";

export interface AegisVerdict {
  /** Payload cleared all six pipeline stages without triggering a veto */
  sanctified:   boolean;
  /** Payload triggered the CONDEMNED terminal rule — block immediately */
  condemned:    boolean;
  /** Highest CorruptionDepth found across all SentinelCells */
  depth:        DepthLabel;
  /** Total Maligna objects detected */
  malignaCount: number;
  /** Whether SanitasSwarm cleaned the payload before forwarding */
  sanitized:    boolean;
  /** Full axiological report text */
  report:       string;
  /** End-to-end pipeline latency in milliseconds */
  latencyMs:    number;
  /** Unique identifier for this adjudication request */
  requestId:    string;
}

// ─── Client options ────────────────────────────────────────────────────────

export interface AegisClientOptions {
  /**
   * Transport backend.
   * "subprocess" — spawns a Python process per call (zero infrastructure, dev/test).
   * "http"       — calls a running Aegis REST server (recommended for production).
   * @default "subprocess"
   */
  transport?: TransportMode;

  /** Python executable path (subprocess mode only). @default "python3" */
  pythonBin?: string;

  /** Absolute path to the Ethos Aegis repo root (subprocess mode). */
  repoRoot?: string;

  /** Full URL to the Aegis REST server, e.g. "https://aegis.myapp.com/v1/adjudicate" */
  serverUrl?: string;

  /** Bearer token for authenticating with the REST server */
  apiKey?: string;

  /** Request timeout in milliseconds. @default 15000 */
  timeoutMs?: number;

  /**
   * When true, throw AegisError instead of returning a condemned verdict.
   * Useful for middleware-style assertion patterns.
   * @default false
   */
  throwOnCondemned?: boolean;

  /** Emit adjudication logs to console. @default false */
  verbose?: boolean;
}

// ─── Guard call ────────────────────────────────────────────────────────────

export interface GuardedCallOptions {
  /** Async function that calls your LLM with the (possibly sanitized) message */
  llmFn: (message: string) => Promise<string>;
  /** Raw user message to adjudicate then forward */
  message: string;
  /** Response returned when the input is condemned. @default "I'm not able to assist with that request." */
  refusalMessage?: string;
}

export interface GuardedCallResult {
  /** Model response text, or refusal message if blocked */
  content: string;
  /** Full adjudication verdict */
  verdict: AegisVerdict;
  /** True if the request was blocked (not forwarded to the LLM) */
  blocked: boolean;
}

// ─── Middleware ────────────────────────────────────────────────────────────

export interface MiddlewareOptions {
  /** Body field to adjudicate. @default "message" */
  field?: string;
}

// ─── Stats ─────────────────────────────────────────────────────────────────

export interface ClientStats {
  adjudications: number;
  blocked:       number;
  sanitized:     number;
  /** Percentage of calls that were blocked, e.g. "3.2%" */
  blockRate:     string;
}

// ─── Errors ────────────────────────────────────────────────────────────────

export class AegisError extends Error {
  readonly name:    "AegisError";
  readonly verdict: AegisVerdict;
  constructor(message: string, verdict: AegisVerdict);
}

export class AegisTransportError extends Error {
  readonly name:   "AegisTransportError";
  readonly cause?: Error;
  constructor(message: string, cause?: Error);
}

// ─── AegisClient ───────────────────────────────────────────────────────────

export class AegisClient {
  constructor(options?: AegisClientOptions);

  /**
   * Run a payload through the full six-stage Ethos Aegis pipeline.
   * @param payload   Raw text to adjudicate
   * @param context   Optional context object forwarded to the pipeline
   */
  adjudicate(
    payload: string,
    context?: Record<string, unknown>
  ): Promise<AegisVerdict>;

  /**
   * Adjudicate and throw AegisError if the result is condemned.
   * Use as a guard assertion at API and service boundaries.
   */
  assertSanctified(payload: string): Promise<AegisVerdict>;

  /**
   * Wrap an LLM call: adjudicate the message first, forward only if safe.
   */
  guard(options: GuardedCallOptions): Promise<GuardedCallResult>;

  /**
   * Express / Fastify / Hono-compatible middleware.
   * Adjudicates req.body[field] and returns HTTP 400 if condemned.
   *
   * @example
   * app.post("/chat", client.middleware(), myHandler);
   * app.post("/ask",  client.middleware({ field: "prompt" }), myHandler);
   */
  middleware(opts?: MiddlewareOptions): (
    req: Record<string, any>,
    res: Record<string, any>,
    next: (err?: any) => void
  ) => void;

  /** Returns aggregate call statistics for this client instance. */
  stats(): ClientStats;
}

// ─── Module-level convenience functions ────────────────────────────────────

/**
 * One-shot adjudication using a shared default subprocess client.
 * Creates the client on first call and reuses it.
 */
export function adjudicate(payload: string): Promise<AegisVerdict>;

/**
 * Adjudicate and throw AegisError if condemned.
 * One-liner guard for use in middleware / request handlers.
 */
export function assertSanctified(payload: string): Promise<AegisVerdict>;
