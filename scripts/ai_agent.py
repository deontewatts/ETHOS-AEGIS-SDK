#!/usr/bin/env python3
"""
NorCal Volley Intel - OpenAI Auto-Fix Agent
Analyzes repo code and applies intelligent fixes via OpenAI API.
"""

import os
import sys
import json
import pathlib
import textwrap
from datetime import datetime
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────────────
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

FIX_MODE     = os.environ.get("FIX_MODE", "full")
REPO_NAME    = os.environ.get("REPO_NAME", "unknown")
PROJECT_TYPE = os.environ.get("PROJECT_TYPE", "generic")
MODEL        = "gpt-4o"

REPORT_DIR = pathlib.Path(".ai-agent")
REPORT_DIR.mkdir(exist_ok=True)

SKIP_DIRS  = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".next", "venv"}
SKIP_EXTS  = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2",
              ".ttf", ".eot", ".mp4", ".mp3", ".zip", ".tar", ".gz", ".lock"}
MAX_FILE_CHARS = 6_000   # per file sent to OpenAI
MAX_FILES      = 30      # max files to include in a single pass

# ── Mode → instructions ──────────────────────────────────────────────────────
MODE_INSTRUCTIONS = {
    "full": """
You are a senior full-stack engineer doing a full audit. For EVERY file:
1. Fix all bugs, syntax errors, logic issues
2. Update deprecated patterns to modern equivalents
3. Refactor for clarity, DRY, and proper separation of concerns
4. Improve error handling and add missing try/catch or guards
5. Clean imports, remove dead code, fix naming conventions
6. Add brief docstrings/comments for complex functions
7. Improve file/folder structure suggestions in the report
""",
    "deps-only": """
You are a dependency manager. Focus only on:
1. Identifying outdated or deprecated package usage in code
2. Flagging insecure dependencies
3. Updating import paths if packages were renamed
4. Removing unused imports
""",
    "bugs-only": """
You are a bug hunter. Focus only on:
1. Runtime errors and unhandled exceptions
2. Off-by-one errors, null/undefined dereferences
3. Async/await issues and promise mishandling
4. Logic errors and incorrect conditionals
5. Missing return statements or wrong return types
""",
    "refactor-only": """
You are a refactoring expert. Focus only on:
1. DRY violations — extract repeated code into functions/classes
2. Long functions — break into smaller, single-responsibility units
3. Magic numbers/strings — replace with named constants
4. Inconsistent naming — standardize to the dominant convention
5. Overly complex conditionals — simplify with early returns or guard clauses
""",
    "structure-only": """
You are an architect. Focus only on:
1. Misplaced files — suggest correct locations
2. Missing index files or barrel exports
3. Inconsistent folder naming conventions
4. Missing or outdated README/docs references
5. Config files that should be centralized
""",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def collect_files(root: pathlib.Path) -> list[pathlib.Path]:
    files = []
    for p in root.rglob("*"):
        if p.is_file():
            if any(skip in p.parts for skip in SKIP_DIRS):
                continue
            if p.suffix.lower() in SKIP_EXTS:
                continue
            files.append(p)
    return sorted(files)[:MAX_FILES]


def read_file_safe(p: pathlib.Path) -> str:
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_FILE_CHARS:
            text = text[:MAX_FILE_CHARS] + f"\n... [TRUNCATED at {MAX_FILE_CHARS} chars]"
        return text
    except Exception as e:
        return f"[ERROR reading file: {e}]"


def build_file_bundle(files: list[pathlib.Path], root: pathlib.Path) -> str:
    parts = []
    for p in files:
        rel = p.relative_to(root)
        content = read_file_safe(p)
        parts.append(f"### FILE: {rel}\n```\n{content}\n```")
    return "\n\n".join(parts)


def call_openai(system_prompt: str, user_content: str) -> str:
    print(f"  → Calling {MODEL}... ", end="", flush=True)
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.15,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content},
        ],
    )
    result = response.choices[0].message.content
    print(f"done ({response.usage.total_tokens} tokens)")
    return result


def parse_fixes(raw: str) -> dict[str, str]:
    """
    Expects OpenAI to return JSON like:
    {
      "fixes": {
        "path/to/file.py": "...full corrected file content...",
        ...
      },
      "summary": "markdown summary of what was changed"
    }
    """
    try:
        # Strip markdown code fences if present
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        data = json.loads(clean)
        return data
    except Exception as e:
        print(f"  ⚠ Could not parse JSON response: {e}")
        return {"fixes": {}, "summary": raw[:2000]}


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n🤖 NorCal Volley Intel AI Agent")
    print(f"   Repo   : {REPO_NAME}")
    print(f"   Mode   : {FIX_MODE}")
    print(f"   Project: {PROJECT_TYPE}")
    print(f"   Time   : {datetime.utcnow().isoformat()}Z\n")

    root = pathlib.Path(".")
    files = collect_files(root)
    print(f"📁 Collected {len(files)} files for analysis")

    if not files:
        print("⚠ No files found. Exiting.")
        sys.exit(0)

    # Build the file bundle to send
    bundle = build_file_bundle(files, root)
    file_list = "\n".join(f"  - {f.relative_to(root)}" for f in files)

    instructions = MODE_INSTRUCTIONS.get(FIX_MODE, MODE_INSTRUCTIONS["full"])

    system_prompt = textwrap.dedent(f"""
        You are an expert software engineer doing a code review and fix pass.
        Repository: {REPO_NAME}
        Project type: {PROJECT_TYPE}
        Fix mode: {FIX_MODE}

        {instructions}

        RESPONSE FORMAT — you MUST return valid JSON only, no prose outside JSON:
        {{
          "fixes": {{
            "relative/path/to/file": "...complete corrected file content (not a diff)...",
            "another/file.js": "..."
          }},
          "summary": "## AI Agent Report\\n\\n### What was fixed\\n...\\n### Files changed\\n...\\n### Recommendations\\n..."
        }}

        Rules:
        - Only include files you ACTUALLY changed in "fixes"
        - "fixes" values must be the FULL corrected file content (not diffs or snippets)
        - Keep the "summary" as clean markdown
        - Do not fabricate new features unless mode is "full"
        - If a file is fine, omit it from "fixes"
        - Never delete critical config files
    """).strip()

    user_content = f"""
Here are the repository files to analyze and fix:

Files included:
{file_list}

---

{bundle}
""".strip()

    print(f"\n🧠 Sending to OpenAI ({FIX_MODE} mode)...")
    raw_response = call_openai(system_prompt, user_content)

    print("\n🔧 Parsing and applying fixes...")
    result = parse_fixes(raw_response)

    fixes   = result.get("fixes", {})
    summary = result.get("summary", "No summary provided.")

    applied = 0
    errors  = 0

    for rel_path, content in fixes.items():
        target = root / rel_path
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"  ✅ Fixed: {rel_path}")
            applied += 1
        except Exception as e:
            print(f"  ❌ Failed to write {rel_path}: {e}")
            errors += 1

    # Write report
    report_path = REPORT_DIR / "report.md"
    report_content = f"""## 🤖 AI Agent Report — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC

**Mode:** `{FIX_MODE}` | **Project:** `{PROJECT_TYPE}` | **Files scanned:** {len(files)}
**Files fixed:** {applied} | **Errors:** {errors}

---

{summary}
"""
    report_path.write_text(report_content, encoding="utf-8")
    print(f"\n📄 Report saved to {report_path}")

    # Write JSON log
    log = {
        "timestamp": datetime.utcnow().isoformat(),
        "repo": REPO_NAME,
        "mode": FIX_MODE,
        "project_type": PROJECT_TYPE,
        "files_scanned": len(files),
        "files_fixed": applied,
        "errors": errors,
        "files_changed": list(fixes.keys()),
    }
    (REPORT_DIR / "run-log.json").write_text(json.dumps(log, indent=2))

    print(f"\n✅ Done! Applied {applied} fixes across {len(files)} files.")
    if errors:
        print(f"⚠ {errors} files had write errors — check permissions.")


if __name__ == "__main__":
    main()
