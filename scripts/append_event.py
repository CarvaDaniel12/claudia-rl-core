#!/usr/bin/env python3
"""
Atomic event appender for BMAD Team RL Core
Appends validated JSON events to contracts/events.jsonl
"""
import sys
import os
import json
import time
import hashlib
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_PATH = Path("contracts/events.schema.json")
EVENTS_PATH = Path("contracts/events.jsonl")
LOCK_PATH = Path("contracts/.events.lock")

def iso_now():
    """Generate ISO 8601 timestamp with Z suffix"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def load_schema():
    """Load JSON schema and jsonschema library"""
    try:
        import jsonschema
    except ImportError:
        print("ERROR: jsonschema not installed. Run: python -m pip install jsonschema", file=sys.stderr)
        sys.exit(2)
    
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    return schema, jsonschema

def validate_event(evt, schema, jsonschema):
    """Validate event against schema"""
    jsonschema.validate(instance=evt, schema=schema)

def atomic_append(line: str):
    """Atomically append line to events.jsonl using lockfile"""
    # Lock by exclusive lockfile
    try:
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        # Simple wait for lock
        for _ in range(100):
            time.sleep(0.05)
            if not LOCK_PATH.exists():
                break
        else:
            print("ERROR: lockfile busy", file=sys.stderr)
            sys.exit(3)
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    
    try:
        with os.fdopen(fd, "w") as _:
            pass
        
        EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with EVENTS_PATH.open("a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
    finally:
        try:
            LOCK_PATH.unlink(missing_ok=True)
        except Exception:
            pass

def main():
    """Main entry point"""
    if len(sys.argv) < 4:
        print("Usage: python scripts/append_event.py <TYPE> <ACTOR> <PAYLOAD_JSON_PATH> [<TIMESTAMP_ISO>]", file=sys.stderr)
        sys.exit(1)
    
    ev_type = sys.argv[1]
    actor = sys.argv[2]
    payload_path = Path(sys.argv[3])
    ts = sys.argv[4] if len(sys.argv) > 4 else iso_now()
    
    if not payload_path.exists():
        print(f"ERROR: payload file not found: {payload_path}", file=sys.stderr)
        sys.exit(1)
    
    with payload_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    
    evt = {"type": ev_type, "timestamp": ts, "actor": actor, "payload": payload}
    
    schema, jsonschema = load_schema()
    try:
        validate_event(evt, schema, jsonschema)
    except Exception as e:
        print(f"ERROR: schema validation failed: {e}", file=sys.stderr)
        sys.exit(2)
    
    # JSON compact one-line
    line = json.dumps(evt, ensure_ascii=False, separators=(",", ":"))
    atomic_append(line)
    
    # Minimal SESSION_LOG.md note
    logline = f"- EVENT {ev_type} by {actor} at {ts} payload={hashlib.sha1(line.encode('utf-8')).hexdigest()[:10]}"
    try:
        with Path("SESSION_LOG.md").open("a", encoding="utf-8") as log:
            log.write(logline + "\n")
    except Exception:
        pass
    
    print("OK")
    sys.exit(0)

if __name__ == "__main__":
    main()

