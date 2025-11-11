#!/usr/bin/env python3
"""
Doc Compiler - Compila shards (.part.md) em um unico documento
Uso: python scripts/compile_docs.py docs/<topic_dir>
Saida: docs/_compiled/<topic>.md
"""
import sys
from pathlib import Path

def compile_topic(topic_dir: Path, out_dir: Path):
    """
    Compila todos os *.part.md de topic_dir em um unico arquivo
    em out_dir/<topic_name>.md, mantendo ordem alfabetica.
    """
    parts = sorted(topic_dir.glob("*.part.md"))
    if not parts:
        print(f"No .part.md in {topic_dir}", file=sys.stderr)
        return 1
    
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{topic_dir.name}.md"
    
    with out_file.open("w", encoding="utf-8") as out:
        for p in parts:
            content = p.read_text(encoding="utf-8")
            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
    
    print(f"Compiled -> {out_file}")
    return 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/compile_docs.py docs/<topic_dir>", file=sys.stderr)
        sys.exit(1)
    
    topic = Path(sys.argv[1])
    if not topic.is_dir():
        print(f"Not a directory: {topic}", file=sys.stderr)
        sys.exit(1)
    
    out_dir = Path("docs/_compiled")
    rc = compile_topic(topic, out_dir)
    sys.exit(rc)

if __name__ == "__main__":
    main()

