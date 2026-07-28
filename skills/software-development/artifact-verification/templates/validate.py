#!/usr/bin/env python3
"""validate.py — Reusable multi-file artifact validator.

Copy this to your project and extend with format-specific checks.

Usage:
    python3 validate.py <file1> [file2 ...]
    python3 validate.py /path/to/dir   (validates all files in directory)
"""

import hashlib, json, os, sys


def validate_file(path):
    if not os.path.exists(path):
        return f"❌ {path} — not found"

    stat = os.stat(path)
    size = stat.st_size
    with open(path, 'rb') as f:
        sha = hashlib.sha256(f.read()).hexdigest()[:16]

    result = {
        "path": path,
        "size": size,
        "sha_prefix": sha,
        "ext": os.path.splitext(path)[1].lower(),
    }

    # Format-specific validation
    ext = result["ext"]
    try:
        if ext == ".json":
            with open(path) as f:
                json.load(f)
            result["format"] = "✅ JSON"
        elif ext == ".py":
            with open(path) as f:
                compile(f.read(), path, "exec")
            result["format"] = "✅ Python"
        elif ext == ".yaml" or ext == ".yml":
            import yaml
            with open(path) as f:
                yaml.safe_load(f)
            result["format"] = "✅ YAML"
        elif ext == ".toml":
            import tomllib
            with open(path, "rb") as f:
                tomllib.load(f)
            result["format"] = "✅ TOML"
        elif ext == ".xml":
            import xml.etree.ElementTree as ET
            ET.parse(path)
            result["format"] = "✅ XML"
        elif ext == ".sh" or ext == ".bash":
            result["format"] = "(shell — run bash -n separately)"
        else:
            result["format"] = "(no validator)"
    except Exception as e:
        result["format"] = f"❌ {e}"

    return result


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["."]
    results = []
    for t in targets:
        if os.path.isdir(t):
            for root, dirs, files in os.walk(t):
                dirs.sort()
                for f in sorted(files):
                    results.append(validate_file(os.path.join(root, f)))
        else:
            results.append(validate_file(t))

    print(f"{'File':<45} {'Size':>8} {'SHA256':<18} {'Format'}")
    print("-" * 85)
    for r in results:
        if isinstance(r, str):
            print(r)
            continue
        name = r["path"][:44]
        size = f"{r['size']} o"
        sha = r["sha_prefix"]
        fmt = r.get("format", "")
        print(f"{name:<45} {size:>8}  {sha:<18} {fmt}")