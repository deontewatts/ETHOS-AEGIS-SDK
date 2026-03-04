// Package aegis provides a Go client for the Ethos Aegis adjudication pipeline.
//
// Two transport modes:
//
//  1. Subprocess — invokes the Python core via os/exec (zero infrastructure, dev/test).
//  2. HTTP       — calls a running Aegis REST server (production recommended).
//
// Quick start (subprocess mode):
//
//	client := aegis.NewClient(nil)
//	verdict, err := client.Adjudicate(ctx, "user payload", nil)
//	if err != nil { log.Fatal(err) }
//	if verdict.Condemned { /* block the request */ }
//
// Quick start (HTTP mode):
//
//	client := aegis.NewClient(&aegis.Options{
//	    Transport: aegis.TransportHTTP,
//	    ServerURL: "https://aegis.myapp.com/v1/adjudicate",
//	    APIKey:    os.Getenv("AEGIS_API_KEY"),
//	})
package aegis

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// ─── Transport ───────────────────────────────────────────────────────────────

// Transport selects the backend used to reach the Aegis pipeline.
type Transport string

const (
	// TransportSubprocess spawns a Python process per call.
	// Good for development, tests, and standalone tooling.
	TransportSubprocess Transport = "subprocess"

	// TransportHTTP calls a running Aegis REST server.
	// Required for production services; supports connection pooling and retries.
	TransportHTTP Transport = "http"
)

// ─── Verdict ─────────────────────────────────────────────────────────────────

// DepthLabel is the five-rung CorruptionDepth name from the Aegis pipeline.
type DepthLabel string

const (
	DepthVoid      DepthLabel = "VOID"
	DepthTrace     DepthLabel = "TRACE"
	DepthCaution   DepthLabel = "CAUTION"
	DepthGrave     DepthLabel = "GRAVE"
	DepthCondemned DepthLabel = "CONDEMNED"
)

// Verdict is the adjudication result returned for every payload.
type Verdict struct {
	// Sanctified is true when the payload cleared all six pipeline stages.
	Sanctified bool `json:"sanctified"`

	// Condemned is true when the FinalityForge compound rule was triggered.
	// Condemned payloads must be blocked; do not forward to the LLM.
	Condemned bool `json:"condemned"`

	// Depth is the highest CorruptionDepth label found across all SentinelCells.
	Depth DepthLabel `json:"depth"`

	// MalignaCount is the total number of Maligna objects detected.
	MalignaCount int `json:"malignaCount"`

	// Sanitized is true when SanitasSwarm cleaned the payload.
	Sanitized bool `json:"sanitized"`

	// Report is the full axiological report from the pipeline.
	Report string `json:"report"`

	// LatencyMs is the end-to-end pipeline latency in milliseconds.
	LatencyMs float64 `json:"latencyMs"`

	// RequestID is a client-generated unique identifier for this adjudication.
	RequestID string `json:"requestId"`
}

// Safe returns true when the payload may be forwarded to the LLM.
// A payload is safe when it is not condemned (CAUTION/VOID are safe).
func (v *Verdict) Safe() bool { return !v.Condemned }

// ─── Errors ──────────────────────────────────────────────────────────────────

// AegisError is returned when a payload is condemned and ThrowOnCondemned is true.
type AegisError struct {
	Verdict *Verdict
	msg     string
}

func (e *AegisError) Error() string { return e.msg }

// TransportError wraps infrastructure-level failures (subprocess crash, HTTP error).
type TransportError struct {
	Cause error
	msg   string
}

func (e *TransportError) Error() string { return e.msg }
func (e *TransportError) Unwrap() error { return e.Cause }

// ─── Options ─────────────────────────────────────────────────────────────────

// Options configure an AegisClient.
type Options struct {
	// Transport backend. Default: TransportSubprocess.
	Transport Transport

	// PythonBin is the Python executable (subprocess mode). Default: "python3".
	PythonBin string

	// RepoRoot is the absolute path to the Ethos Aegis repository root.
	// If empty, the SDK attempts to resolve it from the Go module path.
	RepoRoot string

	// ServerURL is the Aegis REST server endpoint (HTTP mode).
	// Example: "https://aegis.myapp.com/v1/adjudicate"
	ServerURL string

	// APIKey is the Bearer token for the REST server (HTTP mode).
	APIKey string

	// Timeout for each adjudication call. Default: 15s.
	Timeout time.Duration

	// MaxRetries is the number of HTTP retry attempts on transient failures.
	// Default: 2. Only used in HTTP mode.
	MaxRetries int

	// ThrowOnCondemned returns an *AegisError instead of a Verdict when condemned.
	// Default: false.
	ThrowOnCondemned bool

	// Verbose emits adjudication logs to stderr.
	Verbose bool

	// HTTPClient allows injecting a custom *http.Client (HTTP mode).
	// If nil, a default client with the configured Timeout is used.
	HTTPClient *http.Client
}

func (o *Options) withDefaults() *Options {
	out := *o
	if out.Transport == "" {
		out.Transport = TransportSubprocess
	}
	if out.PythonBin == "" {
		out.PythonBin = "python3"
	}
	if out.Timeout == 0 {
		out.Timeout = 15 * time.Second
	}
	if out.MaxRetries == 0 {
		out.MaxRetries = 2
	}
	if out.ServerURL == "" {
		out.ServerURL = "http://localhost:8080/v1/adjudicate"
	}
	if out.RepoRoot == "" {
		out.RepoRoot = defaultRepoRoot()
	}
	if out.HTTPClient == nil && out.Transport == TransportHTTP {
		out.HTTPClient = &http.Client{Timeout: out.Timeout}
	}
	return &out
}

// defaultRepoRoot returns the path four directories above this source file.
// sdk/go/aegis/client.go → sdk/go/aegis → sdk/go → sdk → repo root
func defaultRepoRoot() string {
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		if cwd, err := os.Getwd(); err == nil {
			return cwd
		}
		return "."
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), "..", "..", ".."))
}

// ─── Stats ────────────────────────────────────────────────────────────────────

// Stats holds aggregate metrics for an AegisClient instance.
type Stats struct {
	Adjudications uint64
	Blocked       uint64
	Sanitized     uint64
}

// BlockRate returns blocked / adjudications as a percentage string.
func (s Stats) BlockRate() string {
	if s.Adjudications == 0 {
		return "0%"
	}
	return fmt.Sprintf("%.1f%%", float64(s.Blocked)/float64(s.Adjudications)*100)
}

// ─── AegisClient ─────────────────────────────────────────────────────────────

// AegisClient sends payloads to the Ethos Aegis pipeline and returns verdicts.
// All methods are safe for concurrent use.
type AegisClient struct {
	opts *Options
	mu   sync.Mutex // guards http client reuse diagnostics only

	adjudications atomic.Uint64
	blocked       atomic.Uint64
	sanitized     atomic.Uint64
}

// NewClient creates a new AegisClient. Pass nil to use all defaults.
func NewClient(opts *Options) *AegisClient {
	if opts == nil {
		opts = &Options{}
	}
	return &AegisClient{opts: opts.withDefaults()}
}

// Adjudicate sends payload through the six-stage pipeline and returns a Verdict.
// context is forwarded to the pipeline (may be nil).
func (c *AegisClient) Adjudicate(
	ctx context.Context,
	payload string,
	context_ map[string]any,
) (*Verdict, error) {
	if ctx == nil {
		ctx = context.Background()
	}
	if context_ == nil {
		context_ = map[string]any{}
	}

	requestID := newRequestID()

	var verdict *Verdict
	var err error

	switch c.opts.Transport {
	case TransportSubprocess:
		verdict, err = c.subprocessAdjudicate(ctx, payload, requestID)
	case TransportHTTP:
		verdict, err = c.httpAdjudicate(ctx, payload, context_, requestID)
	default:
		return nil, &TransportError{msg: fmt.Sprintf("unknown transport: %s", c.opts.Transport)}
	}

	if err != nil {
		return nil, err
	}
	verdict.RequestID = requestID

	c.adjudications.Add(1)
	if verdict.Condemned {
		c.blocked.Add(1)
	}
	if verdict.Sanitized {
		c.sanitized.Add(1)
	}

	if c.opts.Verbose {
		fmt.Fprintf(os.Stderr, "[AegisClient] #%s depth=%s sanctified=%v %.2fms\n",
			requestID, verdict.Depth, verdict.Sanctified, verdict.LatencyMs)
	}

	if c.opts.ThrowOnCondemned && verdict.Condemned {
		return nil, &AegisError{
			Verdict: verdict,
			msg:     fmt.Sprintf("[EthosAegis] payload CONDEMNED at depth %s", verdict.Depth),
		}
	}

	return verdict, nil
}

// AssertSanctified adjudicates and returns *AegisError if condemned.
// Use as a guard assertion at service boundaries.
func (c *AegisClient) AssertSanctified(ctx context.Context, payload string) (*Verdict, error) {
	v, err := c.Adjudicate(ctx, payload, nil)
	if err != nil {
		return nil, err
	}
	if v.Condemned {
		return nil, &AegisError{
			Verdict: v,
			msg:     fmt.Sprintf("[EthosAegis] payload CONDEMNED at depth %s", v.Depth),
		}
	}
	return v, nil
}

// Guard adjudicates payload, then calls llmFn only if safe.
// Returns (llmResponse, verdict, blocked, error).
func (c *AegisClient) Guard(
	ctx context.Context,
	payload string,
	llmFn func(ctx context.Context, msg string) (string, error),
	refusal string,
) (string, *Verdict, bool, error) {
	if refusal == "" {
		refusal = "I'm not able to assist with that request."
	}

	v, err := c.Adjudicate(ctx, payload, nil)
	if err != nil {
		return "", nil, false, err
	}
	if v.Condemned {
		return refusal, v, true, nil
	}

	response, err := llmFn(ctx, payload)
	if err != nil {
		return "", v, false, err
	}
	return response, v, false, nil
}

// Stats returns aggregate call statistics for this client instance.
func (c *AegisClient) Stats() Stats {
	return Stats{
		Adjudications: c.adjudications.Load(),
		Blocked:       c.blocked.Load(),
		Sanitized:     c.sanitized.Load(),
	}
}

// ─── Subprocess transport ────────────────────────────────────────────────────

func (c *AegisClient) subprocessAdjudicate(
	ctx context.Context,
	payload, requestID string,
) (*Verdict, error) {
	script := strings.Join([]string{
		"import sys, json, os, time as _t",
		fmt.Sprintf("sys.path.insert(0, %q)", c.opts.RepoRoot),
		"from ethos_aegis import EthosAegis",
		"a = EthosAegis()",
		"p = os.environ['_AEGIS_PAYLOAD']",
		"t0 = _t.perf_counter()",
		"v = a.adjudicate(p)",
		"ms = (_t.perf_counter() - t0) * 1000",
		`print(json.dumps({` +
			`'sanctified': v.is_sanctified,` +
			`'condemned':  v.is_condemned,` +
			`'depth':      v.sovereignty_depth.name,` +
			`'malignaCount': len(v.maligna_found),` +
			`'sanitized':  v.purified_payload is not None,` +
			`'report':     v.axiological_report,` +
			`'latencyMs':  round(ms, 2),` +
			`}))`,
	}, "\n")

	cmd := exec.CommandContext(ctx, c.opts.PythonBin, "-c", script)
	cmd.Env = append(os.Environ(),
		"_AEGIS_PAYLOAD="+payload,
		"AEGIS_LOG_LEVEL=ERROR",
	)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return nil, &TransportError{
			Cause: err,
			msg:   fmt.Sprintf("subprocess failed: %v — stderr: %s", err, stderr.String()[:min(200, stderr.Len())]),
		}
	}

	var v Verdict
	if err := json.Unmarshal(bytes.TrimSpace(stdout.Bytes()), &v); err != nil {
		return nil, &TransportError{
			Cause: err,
			msg:   fmt.Sprintf("JSON parse failed: %v — raw: %s", err, stdout.String()[:min(200, stdout.Len())]),
		}
	}
	return &v, nil
}

// ─── HTTP transport ──────────────────────────────────────────────────────────

type httpRequest struct {
	Payload   string         `json:"payload"`
	Context   map[string]any `json:"context"`
	RequestID string         `json:"request_id"`
}

func (c *AegisClient) httpAdjudicate(
	ctx context.Context,
	payload string,
	context_ map[string]any,
	requestID string,
) (*Verdict, error) {
	body, err := json.Marshal(httpRequest{
		Payload:   payload,
		Context:   context_,
		RequestID: requestID,
	})
	if err != nil {
		return nil, &TransportError{msg: "marshal error: " + err.Error(), Cause: err}
	}

	var lastErr error
	for attempt := 0; attempt <= c.opts.MaxRetries; attempt++ {
		if attempt > 0 {
			// Exponential backoff: 100ms, 200ms, 400ms…
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(time.Duration(100<<attempt) * time.Millisecond):
			}
		}

		req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.opts.ServerURL, bytes.NewReader(body))
		if err != nil {
			return nil, &TransportError{msg: "request build error: " + err.Error(), Cause: err}
		}
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-Request-ID", requestID)
		if c.opts.APIKey != "" {
			req.Header.Set("Authorization", "Bearer "+c.opts.APIKey)
		}

		resp, err := c.opts.HTTPClient.Do(req)
		if err != nil {
			lastErr = &TransportError{msg: "HTTP request failed: " + err.Error(), Cause: err}
			continue
		}
		defer resp.Body.Close()

		raw, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
		if err != nil {
			lastErr = &TransportError{msg: "read response failed: " + err.Error(), Cause: err}
			continue
		}

		if resp.StatusCode >= 500 {
			lastErr = &TransportError{msg: fmt.Sprintf("server error %d: %s", resp.StatusCode, string(raw)[:min(200, len(raw))])}
			continue
		}

		var v Verdict
		if err := json.Unmarshal(raw, &v); err != nil {
			return nil, &TransportError{msg: "JSON parse failed: " + err.Error(), Cause: err}
		}
		return &v, nil
	}

	return nil, lastErr
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

func newRequestID() string {
	b := make([]byte, 8)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
