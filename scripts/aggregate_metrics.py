#!/usr/bin/env python3
"""
Aggregate Metrics - Consolida metricas de run em evolution.json
Uso: python scripts/aggregate_metrics.py <run_data.json>
"""
import json
import sys
import time
import os
from pathlib import Path
from datetime import datetime, timezone

EVOLUTION_PATH = Path("rl_atomic/evolution.json")
LOCK_PATH = Path("rl_atomic/.evolution.lock")
RUN_DATA_SCHEMA = Path("contracts/run_data_schema.json")

def load_schema():
    """Carrega schema de validacao"""
    try:
        import jsonschema
    except ImportError:
        print("ERROR: jsonschema not installed. Run: pip install jsonschema", 
              file=sys.stderr)
        sys.exit(2)
    
    with RUN_DATA_SCHEMA.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    return schema, jsonschema

def validate_run_data(data, schema, jsonschema):
    """Valida run_data contra schema"""
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True
    except Exception as e:
        print(f"ERROR: Schema validation failed: {e}", file=sys.stderr)
        return False

def acquire_lock(timeout=10):
    """Adquire lock exclusivo com timeout"""
    start = time.time()
    while True:
        try:
            fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True
        except FileExistsError:
            if time.time() - start > timeout:
                print("ERROR: Lock timeout", file=sys.stderr)
                return False
            time.sleep(0.1)

def release_lock():
    """Libera lock"""
    try:
        LOCK_PATH.unlink(missing_ok=True)
    except Exception:
        pass

def load_evolution():
    """Carrega evolution.json"""
    if not EVOLUTION_PATH.exists():
        return {
            "schema_version": "1.0",
            "description": "Serie temporal de metricas de runs RL Atomica",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "runs": []
        }
    
    with EVOLUTION_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_evolution(data):
    """Salva evolution.json"""
    EVOLUTION_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    backup = Path(f"rl_atomic/backups/evolution_{int(time.time())}.json")
    backup.parent.mkdir(parents=True, exist_ok=True)
    if EVOLUTION_PATH.exists():
        with EVOLUTION_PATH.open("r") as src, backup.open("w") as dst:
            dst.write(src.read())
    
    with EVOLUTION_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    cleanup_old_backups(backup.parent, keep=3)

def cleanup_old_backups(backup_dir, keep=3):
    """Mantem apenas os ultimos N backups"""
    backups = sorted(backup_dir.glob("evolution_*.json"), 
                     key=lambda p: p.stat().st_mtime, 
                     reverse=True)
    for old in backups[keep:]:
        old.unlink()

def append_run(evolution, run_data):
    """Adiciona run ao evolution"""
    if run_data["run_id"] in [r["run_id"] for r in evolution["runs"]]:
        print(f"WARNING: run_id {run_data['run_id']} already exists, skipping", 
              file=sys.stderr)
        return False
    
    evolution["runs"].append(run_data)
    evolution["last_updated"] = datetime.now(timezone.utc).isoformat()
    return True

def publish_event(run_data):
    """Publica evento METRICS_UPDATED"""
    payload = {
        "run_id": run_data["run_id"],
        "reward": run_data["reward"],
        "pass_rate": run_data["assertions_pass_rate"],
        "duration_s": run_data["duration_s"]
    }
    
    payload_path = Path("payloads/metrics_updated_temp.json")
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    with payload_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    
    import subprocess
    cmd = [
        "python", "scripts/append_event.py",
        "METRICS_UPDATED", "Data-Specialist",
        str(payload_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    payload_path.unlink(missing_ok=True)
    
    if result.returncode != 0:
        print(f"WARNING: Event publication failed: {result.stderr}", 
              file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/aggregate_metrics.py <run_data.json>", 
              file=sys.stderr)
        sys.exit(1)
    
    run_data_path = Path(sys.argv[1])
    if not run_data_path.exists():
        print(f"ERROR: File not found: {run_data_path}", file=sys.stderr)
        sys.exit(1)
    
    with run_data_path.open("r", encoding="utf-8") as f:
        run_data = json.load(f)
    
    schema, jsonschema = load_schema()
    if not validate_run_data(run_data, schema, jsonschema):
        sys.exit(2)
    
    if not acquire_lock():
        sys.exit(3)
    
    try:
        evolution = load_evolution()
        if append_run(evolution, run_data):
            save_evolution(evolution)
            print(f"OK: Added {run_data['run_id']} to evolution.json")
            publish_event(run_data)
        else:
            print("SKIPPED: Run already exists")
    finally:
        release_lock()
    
    sys.exit(0)

if __name__ == "__main__":
    main()

