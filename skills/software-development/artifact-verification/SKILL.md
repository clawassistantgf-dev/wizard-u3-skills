---
name: artifact-verification
description: "Verify file/artifact integrity after creation: checksums, format validation, syntax checks, directory-level hashes. For ad-hoc quality gates outside a git context."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [verification, integrity, validation, quality, checksum, file-ops]
    related_skills: [requesting-code-review, spike, test-driven-development]
---

# Artifact Verification

Use this skill when you've created files (configs, scripts, data, outputs) and need to verify their integrity — checksums, format validity, syntax correctness, or directory-level consistency. This is the **ad-hoc quality gate** outside a git context (for git-bound verification, use `requesting-code-review`).

## When to Use

- After creating multiple files of different types in a single burst (scripts + configs + data)
- When the user explicitly asks to "validate" or "verify" files they just asked you to create
- Before delivering artifacts to the user via file upload, email, or archiving
- After downloading/extracting toolchains or archives — verify they aren't corrupt
- When debugging "file not found" or "wrong checksum" issues

**Don't use this for:** git pre-commit verification (use `requesting-code-review`), or full TDD test suites (use `test-driven-development`).

## Core Method

Every verification follows this pattern:

```
create  →  inspect  →  checksum  →  format-validate  →  hash-dir  →  report
```

### 1. Create (the artifacts)

Write all files first. Batch independent writes with parallel tool calls.

### 2. Inspect

Check each file exists and has non-zero size. Use a single terminal command:

```bash
find /path -type f -name "*.json" -o -name "*.py" | sort | while read f; do
  printf "  %-40s %5s octets\n" "$(basename $f)" "$(stat -c'%s' $f)"
done
```

### 3. Checksum

Generate SHA256 for each file. Batch into one command:

```bash
sha256sum /path/*.txt /path/*.json /path/*.py /path/*.yaml /path/*.md 2>/dev/null
```

### 4. Format validation

Run type-appropriate validators per file format:

| Format  | Command                                                                |
|---------|------------------------------------------------------------------------|
| JSON    | `python3 -m json.tool file.json > /dev/null && echo "✅ JSON valide"`  |
| YAML    | `python3 -c "import yaml; yaml.safe_load(open('file.yaml'))"`          |
| TOML    | `python3 -c "import tomllib; tomllib.load(open('file.toml','rb'))"`    |
| Python  | `python3 -m py_compile file.py`                                        |
| Shell   | `bash -n file.sh`                                                      |
| Markdown | (visual only — no standard linter without plugins)                    |
| XML     | `python3 -c "import xml.etree.ElementTree as ET; ET.parse('file.xml')"` |

### 5. Directory-level hash

Generate a single integrity fingerprint for the entire directory. This detects any file that was added, removed, or modified:

```bash
tar cf - /path/to/dir 2>/dev/null | sha256sum | cut -c1-16
```

This is more useful than individual file hashes for a final "did anything change?" check.

### 6. Report

Present results in a compact table:

```
| File           | Size   | SHA256 (prefix) | Format  | Status |
|----------------|--------|-----------------|---------|--------|
| config.json    | 262 o  | ce68e731…       | JSON    | ✅     |
| ritual.py      | 795 o  | ebb9cc0e…       | Python  | ✅     |
| manifest.yaml  | 279 o  | f6bc42fd…       | YAML    | ✅     |
```

## Custom validation script (templates/validate.py)

The skill ships with a reusable validation script. Copy it to your project and extend as needed:

- `templates/validate.py` — General-purpose file validator. Supports JSON, Python, YAML, TOML, XML format checks, SHA256 hashing, and recursive directory scanning. Load with `skill_view(name='artifact-verification', file_path='templates/validate.py')` then copy with `write_file`.

## Session reference

- `references/session-2026-07-05-rust-and-validation.md` — Exact commands from this session: multi-file validation sweep, Rust installation on constrained systems, disk space troubleshooting, and Python `getlogin()` fallback for containerized environments.

## Background installation pattern

When installing a large toolchain (Rust, Node, etc.) on a space-constrained system:

1. **Profile minimal** — Always pass `--profile minimal` to rustup (or `--no-optional-deps` for npm) to strip docs, examples, and extra components
2. **Background process** — Run the installer with `terminal(background=true, notify_on_complete=true)` and continue working while it downloads
3. **Poll for completion** — Use `process(action='poll')` to check status, then source the env and verify with `--version`
4. **Fallback to apt** — If rustup fails (space, network), try `apt-get download` + manual `.deb` extraction of just `rustc`. Note: Debian's rustc package is split into shared libs, so extraction alone won't work without `sudo apt-get install`.

### Rust-specific sequence

```bash
# Install (background, minimal profile)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- \
  -y --default-toolchain stable --profile minimal

# Activate
. "$HOME/.cargo/env"

# Verify
rustc --version
cargo --version

# Compile and run
rustc hello.rs -o /tmp/hello && /tmp/hello
```

## Pitfalls

- **Disk space** — Always check `df -h /` before downloading large toolchains. The official Rust tarball is ~360MB compressed; extracting needs ~1GB free. Profile-minimal helps.
- **Network timeouts** — Large downloads from `static.rust-lang.org` can be slow. Use background mode with `notify_on_complete=true` and a generous timeout.
- **Debian .deb packages** — The `rustc` .deb is only 15K because it's a wrapper; the real compiler is in split library packages (`librustc-driver-*`). Don't try to extract it without sudo.
- **getlogin() in containers** — `os.getlogin()` may fail with `OSError: Unknown error -25` in environments without utmp. Use `os.environ.get('USER') or os.environ.get('LOGNAME')` instead.
- **Working directory after `rm -rf`** — If you delete the cwd, subsequent `pwd && ls` will fail with exit code 2. Always `cd /home/user` after cleaning up temp dirs.