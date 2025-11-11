#!/usr/bin/env python3
"""
Diff Guard - Valida limites de diff por tipo de arquivo
Baseado em contracts/diff_policy.json
"""
import json
import sys
import subprocess
import fnmatch
from pathlib import Path

def load_policy(path):
    """Carrega política de diffs de arquivo JSON"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def git_diff_added_lines(base_ref):
    """
    Retorna dict {file: added_line_count} contando linhas adicionadas
    no diff entre base_ref e HEAD
    """
    cmd = ["git", "diff", "--unified=0", f"{base_ref}...HEAD"]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if p.returncode not in (0, 1):
        print("ERROR: git diff failed", file=sys.stderr)
        sys.exit(2)
    
    lines = p.stdout.splitlines()
    added = {}
    cur = None
    
    for ln in lines:
        if ln.startswith("+++ "):
            path = ln[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            cur = path
            added.setdefault(cur, 0)
        elif ln.startswith("@@"):
            # hunk header, ignore
            pass
        elif ln.startswith("+") and not ln.startswith("+++"):
            if cur:
                added[cur] = added.get(cur, 0) + 1
    
    return added

def cap_for(path, caps):
    """
    Encontra o primeiro glob que casa com path e retorna max_lines.
    Fallback: 200 linhas.
    """
    for item in caps:
        if fnmatch.fnmatch(path, item["glob"]):
            return int(item["max_lines"])
    return 200

def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Valida limites de diff por tipo de arquivo"
    )
    ap.add_argument("--base", default="origin/main", 
                    help="Base ref para comparação (default: origin/main)")
    ap.add_argument("--policy", default="contracts/diff_policy.json",
                    help="Caminho para diff_policy.json")
    args = ap.parse_args()
    
    if not Path(args.policy).exists():
        print("No policy found; default 200 lines per file.", file=sys.stderr)
        policy = {"caps": [{"glob": "**", "max_lines": 200}]}
    else:
        policy = load_policy(args.policy)
    
    caps = policy.get("caps", [])
    added = git_diff_added_lines(args.base)
    
    ok = True
    for fpath, n in added.items():
        if n <= 0:
            continue
        
        limit = cap_for(fpath, caps)
        if n > limit:
            print(f"VIOLATION: {fpath} added {n} > cap {limit}", file=sys.stderr)
            ok = False
        else:
            print(f"OK: {fpath} added {n} <= cap {limit}")
    
    if not ok:
        sys.exit(3)
    
    print("diff_guard OK")
    sys.exit(0)

if __name__ == "__main__":
    main()

