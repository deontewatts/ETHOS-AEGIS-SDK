# Ethos Aegis — SDK Reference

Multi-language SDK for the **Ethos Aegis Sovereign Integrity Mesh**.
Wrap any AI model with a six-stage biological immune pipeline.

---

## Language Support

| SDK | Transport | Streaming | Adapters | Location |
|-----|-----------|-----------|----------|----------|
| **Python** (pip) | Embedded · HTTP | ✓ | OpenAI · Anthropic · Mistral · Gemini · Generic | `sdk/python/` |
| **Node.js** | Subprocess · HTTP | ✓ (ESM/CJS) | — | `sdk/node/` |
| **Go** | Subprocess · HTTP | planned | — | `sdk/go/` |
| **Rust** | Subprocess · HTTP | planned | PyO3 ext | `sdk/rust/` |

---

## Python SDK

### Install

```bash
pip install -e sdk/python                   # development (repo)
pip install ethos-aegis-sdk                 # once published to PyPI

# optional provider adapters
pip install ethos-aegis-sdk[openai]         # + openai>=1.0
pip install ethos-aegis-sdk[anthropic]      # + anthropic>=0.25
pip install ethos-aegis-sdk[mistral]        # + mistralai>=1.0
pip install ethos-aegis-sdk[gemini]         # + google-generativeai>=0.7
pip install ethos-aegis-sdk[all]            # all providers
```

### Usage

```python
from ethos_aegis_sdk import AegisClient

# Embedded mode (fastest — same Python process)
client = AegisClient()

verdict = client.adjudicate("user message")
print(verdict.is_sanctified, verdict.sovereignty_depth)

# Guard an LLM call
response = client.guard(
    message="user question",
    llm_fn=lambda msg: your_llm.complete(msg),
)
print(response.content, response.was_blocked)

# HTTP mode (separate Aegis server)
client = AegisClient(
    transport="http",
    server_url="https://aegis.myapp.com/v1/adjudicate",
    api_key=os.getenv("AEGIS_API_KEY"),
)
```

### UniversalGuard — wrap any AI model

```python
from ethos_aegis_sdk import AegisClient
from ethos_aegis.agent import UniversalGuard
from ethos_aegis.agent.adapters import (
    OpenAIAdapter, AnthropicAdapter, MistralAdapter,
    GeminiAdapter, GenericAdapter,
)

# OpenAI / Azure OpenAI / OpenRouter / Groq
guard = UniversalGuard(
    adapter=OpenAIAdapter(api_key="sk-...", model="gpt-4o"),
    auto_evolve=True,
)
response = guard.chat("user input")

# Anthropic Claude
guard = UniversalGuard(
    adapter=AnthropicAdapter(api_key="sk-ant-...", model="claude-sonnet-4-6"),
)

# Mistral
guard = UniversalGuard(
    adapter=MistralAdapter(api_key="...", model="mistral-large-latest"),
)

# Google Gemini
guard = UniversalGuard(
    adapter=GeminiAdapter(api_key="AIza...", model="gemini-1.5-pro"),
)

# Local Ollama / llama.cpp / vLLM (zero external deps)
guard = UniversalGuard(
    adapter=GenericAdapter(base_url="http://localhost:11434/v1", model="llama3"),
)

# Streaming
for chunk in guard.stream_chat("tell me about Python"):
    print(chunk, end="", flush=True)

print(guard.stats())
```

### GenesisEngine — autonomous pattern evolution

```python
client = AegisClient(auto_evolve=True, evolve_every_n=25)
# After 25 adjudications, GenesisEngine automatically:
#   1. Harvests confirmed threats from MnemosyneCache
#   2. Mutates them into new detection patterns (synonym + injection + boundary)
#   3. Injects top patterns into VanguardProbe

report = client.evolve()  # manual trigger
print(report)
```

---

## Node.js SDK

### Install

```bash
cd sdk/node
# no npm dependencies for subprocess mode
node --version  # ≥ 18 required
```

### Usage (CJS)

```js
const { AegisClient, AegisError } = require("@ethos-aegis/sdk");

const client = new AegisClient({ verbose: true });

// Adjudicate
const verdict = await client.adjudicate("user message");
console.log(verdict.sanctified, verdict.depth);

// Guard an LLM call
const result = await client.guard({
  message: "user input",
  llmFn: async (msg) => await myLLM.complete(msg),
});

// Express middleware
app.post("/chat", client.middleware(), handler);

// Throw on condemned
const strictClient = new AegisClient({ throwOnCondemned: true });
try {
  await strictClient.adjudicate("suspicious payload");
} catch (err) {
  if (err instanceof AegisError) console.log("Blocked:", err.verdict.depth);
}
```

### Usage (ESM / TypeScript)

```ts
import { AegisClient, AegisVerdict } from "@ethos-aegis/sdk";

const client = new AegisClient({ transport: "subprocess" });
const verdict: AegisVerdict = await client.adjudicate("hello");
```

### HTTP mode

```js
const client = new AegisClient({
  transport: "http",
  serverUrl: "https://aegis.myapp.com/v1/adjudicate",
  apiKey: process.env.AEGIS_API_KEY,
  timeoutMs: 10_000,
});
```

### Run tests

```bash
cd sdk/node
node --test tests/
```

---

## Go SDK

### Install

```bash
cd sdk/go
go mod tidy
```

### Usage

```go
package main

import (
    "context"
    "fmt"
    "log"
    "github.com/ethos-aegis/sdk-go/aegis"
)

func main() {
    // Subprocess (dev/test)
    client := aegis.NewClient(nil)
    verdict, err := client.Adjudicate(context.Background(), "user message", nil)
    if err != nil { log.Fatal(err) }
    fmt.Println(verdict.Sanctified, verdict.Depth)

    // HTTP (production)
    client = aegis.NewClient(&aegis.Options{
        Transport: aegis.TransportHTTP,
        ServerURL: "https://aegis.myapp.com/v1/adjudicate",
        APIKey:    os.Getenv("AEGIS_API_KEY"),
        MaxRetries: 3,
    })

    // Guard pattern
    response, verdict, blocked, err := client.Guard(
        context.Background(),
        "user message",
        func(ctx context.Context, msg string) (string, error) {
            return yourLLM.Complete(ctx, msg)
        },
        "",
    )
    _ = response; _ = verdict; _ = blocked

    // Assert sanctified
    if _, err := client.AssertSanctified(context.Background(), payload); err != nil {
        var ae *aegis.AegisError
        if errors.As(err, &ae) {
            log.Printf("Condemned at depth %s", ae.Verdict.Depth)
        }
    }

    // Stats
    fmt.Println(client.Stats().BlockRate())
}
```

### Run tests

```bash
cd sdk/go
go test ./tests/... -v -timeout 120s
```

---

## Rust SDK

### Install

```toml
# Cargo.toml
[dependencies]
ethos-aegis-sdk = { path = "sdk/rust" }
```

### Usage

```rust
use ethos_aegis_sdk::{AegisClient, ClientOptions, Transport};

fn main() {
    // Subprocess (dev/test)
    let client = AegisClient::default_client();
    let verdict = client.adjudicate("user message", None).unwrap();
    println!("{} {:?}", verdict.sanctified, verdict.depth);

    // HTTP (production)
    let client = AegisClient::new(ClientOptions {
        transport:  Transport::Http,
        server_url: Some("https://aegis.myapp.com/v1/adjudicate".into()),
        api_key:    Some(std::env::var("AEGIS_API_KEY").unwrap()),
        ..Default::default()
    });

    // Guard
    let (response, verdict, blocked) = client.guard(
        "user message",
        |msg| Ok(your_llm.complete(msg)),
        None,
    ).unwrap();

    // CLI tool
    // echo "payload" | cargo run --bin aegis-guard

    // Stats
    println!("{}", client.stats().block_rate());
}
```

### Run tests

```bash
cd sdk/rust
cargo test -- --test-threads=1
```

### PyO3 extension (call Rust from Python)

```bash
pip install maturin
cd sdk/rust
maturin develop --features pyo3-ext

# Then in Python:
import ethos_aegis_sdk
result = ethos_aegis_sdk.adjudicate("payload")  # returns JSON string
```

---

## Adapter Matrix

| Adapter | Provider | pip install | Notes |
|---------|----------|-------------|-------|
| `OpenAIAdapter` | OpenAI, Azure OpenAI, OpenRouter, Groq, Together AI, Anyscale | `openai>=1.0` | `base_url` override for compatible endpoints |
| `AnthropicAdapter` | Anthropic Claude | `anthropic>=0.25` | Streaming ✓ |
| `MistralAdapter` | Mistral AI Cloud, self-hosted | `mistralai>=1.0` | Streaming ✓ |
| `GeminiAdapter` | Google AI Studio | `google-generativeai>=0.7` | Streaming ✓ |
| `GeminiVertexAdapter` | Google Vertex AI | `google-cloud-aiplatform>=1.50` | Enterprise, regional |
| `GenericAdapter` | Ollama, llama.cpp, vLLM, LM Studio | *(none)* | Zero deps, HTTP/1.1 |

---

## Verdict Reference

```
AegisVerdict
├── is_sanctified       bool   — passed all six stages
├── is_condemned        bool   — triggered CONDEMNED terminal rule
├── sovereignty_depth   CorruptionDepth   VOID | TRACE | CAUTION | GRAVE | CONDEMNED
├── maligna_found       list[Malignum]    — all threats detected
├── purified_payload    str | None        — SanitasSwarm-cleaned version
├── axiological_report  str               — human-readable moral report
└── adjudication_time   float             — seconds
```

## SentinelCell Pipeline

```
Input ──► VanguardProbe  (regex sentry — override / DAN / privilege / exfil)
       ──► LogosScythe   (semantic arbiter — gaslighting / authority forgery)
       ──► MnemosyneCache (antibody memory — known threat fingerprints)
       ──► SanitasSwarm  (sanitizer — invisible chars / homoglyphs / markup)
       ──► EntropicWatch (resource guard — repetition / token flood / entropy)
       ──► TaintBeacon   (ethics alarm — self-harm / radicalization / hate)
       ──► FinalityForge (compound rule — 3× GRAVE or 1× CONDEMNED → block)
       ──► Verdict
```
