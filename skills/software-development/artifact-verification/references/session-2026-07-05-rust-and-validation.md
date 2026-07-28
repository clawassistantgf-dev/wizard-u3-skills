# Session Reference: 2026-07-05 — Rust + Multi-File Validation

## Scenario

User requested: write a test file, then add files to validate, then run Python hello world, then run Rust code.

## Commands used

### Parallel file creation
```bash
# 4 files created concurrently with write_file tool
# Types: JSON (config.json), Python (ritual.py), YAML (manifest.yaml), Markdown (README.md)
```

### Multi-file validation sweep
```bash
# Individual validation via custom script
python3 ritual.py test.txt config.json ritual.py manifest.yaml README.md

# JSON syntax check
python3 -m json.tool config.json > /dev/null && echo "✅ JSON valide"

# Python syntax check
python3 -m py_compile ritual.py && echo "✅ Python syntaxe OK"

# SHA256 checksums
sha256sum *.txt *.json *.py *.yaml *.md

# Directory-level integrity fingerprint
tar cf - /path/to/dir 2>/dev/null | sha256sum | cut -c1-16

# Full file listing with sizes
find /path -type f | sort | while read f; do
  echo "  $(stat -c'%s' "$f") octets  —  $f"
done
```

### Rust installation (constrained system)
```bash
# Minimal profile — no docs, no clippy, no rustfmt
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- \
  -y --default-toolchain stable --profile minimal

# Activate
. "$HOME/.cargo/env"

# Verify
rustc --version   # rustc 1.96.1
cargo --version   # cargo 1.96.1

# Compile & run
rustc hello.rs -o /tmp/hello && /tmp/hello
```

### Disk space troubleshooting
```bash
df -h /
du -sh /home/* /var/cache /var/log /usr/lib /usr/share | sort -rh
sudo apt-get clean -y
sudo journalctl --vacuum-time=1d
sudo rm -rf /var/cache/apt/archives/*.deb
```

### Python hello world (getlogin() fallback)
```python
# getlogin() fails in containerized environments
# Use env vars instead:
user = os.environ.get('USER') or os.environ.get('LOGNAME') or 'mortal'
```