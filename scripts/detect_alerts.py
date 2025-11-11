#!/usr/bin/env python3
"""
Detect Alerts - Detecta alertas baseado em thresholds
Uso: python scripts/detect_alerts.py [<run_id>]
Se run_id omitido, usa ultimo run de evolution.json
"""
import json
import sys
from pathlib import Path
from datetime import datetime

EVOLUTION_PATH = Path("rl_atomic/evolution.json")
ALERT_CONFIG_PATH = Path("contracts/alert_config.json")
ALERTS_PATH = Path("reports/alerts.md")

def load_evolution():
    """Carrega evolution.json"""
    if not EVOLUTION_PATH.exists():
        print("ERROR: evolution.json not found", file=sys.stderr)
        sys.exit(1)
    
    with EVOLUTION_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_alert_config():
    """Carrega configuracao de alertas"""
    if not ALERT_CONFIG_PATH.exists():
        print("ERROR: alert_config.json not found", file=sys.stderr)
        sys.exit(1)
    
    with ALERT_CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def get_run(evolution, run_id=None):
    """Retorna run especifico ou ultimo"""
    runs = evolution["runs"]
    if not runs:
        print("ERROR: No runs available", file=sys.stderr)
        sys.exit(1)
    
    if run_id:
        for r in runs:
            if r["run_id"] == run_id:
                return r
        print(f"ERROR: Run {run_id} not found", file=sys.stderr)
        sys.exit(1)
    
    return runs[-1]

def check_thresholds(run, config):
    """Verifica thresholds e retorna lista de alertas"""
    thresholds = config["thresholds"]
    alerts = []
    
    if run["assertions_pass_rate"] < thresholds["pass_rate_min"]["value"]:
        alerts.append({
            "metric": "assertions_pass_rate",
            "value": run["assertions_pass_rate"],
            "threshold": thresholds["pass_rate_min"]["value"],
            "severity": thresholds["pass_rate_min"]["severity"],
            "condition": "<"
        })
    
    if run["reward"] < thresholds["reward_min"]["value"]:
        alerts.append({
            "metric": "reward",
            "value": run["reward"],
            "threshold": thresholds["reward_min"]["value"],
            "severity": thresholds["reward_min"]["severity"],
            "condition": "<"
        })
    
    if run["duration_s"] > thresholds["duration_max"]["value"]:
        alerts.append({
            "metric": "duration_s",
            "value": run["duration_s"],
            "threshold": thresholds["duration_max"]["value"],
            "severity": thresholds["duration_max"]["severity"],
            "condition": ">"
        })
    
    if run["selector_success_rate"] < thresholds["selector_success_rate_min"]["value"]:
        alerts.append({
            "metric": "selector_success_rate",
            "value": run["selector_success_rate"],
            "threshold": thresholds["selector_success_rate_min"]["value"],
            "severity": thresholds["selector_success_rate_min"]["severity"],
            "condition": "<"
        })
    
    return alerts

def format_alert(alert, run, config):
    """Formata alerta para markdown"""
    fmt = config["alert_format"]
    severity_info = config["severities"][alert["severity"]]
    
    lines = []
    lines.append(f"### {alert['severity'].upper()}: {alert['metric']} {alert['condition']} threshold\n")
    lines.append(f"- **Run**: {run['run_id']}\n")
    lines.append(f"- **Timestamp**: {run['timestamp']}\n")
    lines.append(f"- **Value**: {alert['value']}\n")
    lines.append(f"- **Threshold**: {alert['threshold']}\n")
    lines.append(f"- **Action**: {severity_info['action']}\n")
    lines.append(f"- **Notify**: {', '.join(severity_info['notify'])}\n")
    lines.append("\n")
    
    return "".join(lines)

def append_alerts(run, alerts, config):
    """Adiciona alertas ao arquivo de alertas"""
    ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if not ALERTS_PATH.exists():
        with ALERTS_PATH.open("w", encoding="utf-8") as f:
            f.write("# Alerts History\n\n")
    
    with ALERTS_PATH.open("a", encoding="utf-8") as f:
        f.write(f"## Run {run['run_id']} - {datetime.now().isoformat()}\n\n")
        
        if not alerts:
            f.write("No alerts detected.\n\n")
        else:
            for alert in alerts:
                f.write(format_alert(alert, run, config))
        
        f.write("---\n\n")

def publish_blocker_event(run, alerts):
    """Publica evento BLOCKER_RAISED se houver alertas criticos"""
    critical = [a for a in alerts if a["severity"] == "critical"]
    if not critical:
        return
    
    payload = {
        "run_id": run["run_id"],
        "blockers": [a["metric"] for a in critical],
        "severity": "critical"
    }
    
    payload_path = Path("payloads/blocker_raised_temp.json")
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    with payload_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    
    import subprocess
    cmd = [
        "python", "scripts/append_event.py",
        "BLOCKER_RAISED", "Data-Specialist",
        str(payload_path)
    ]
    subprocess.run(cmd, capture_output=True)
    
    payload_path.unlink(missing_ok=True)

def main():
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    evolution = load_evolution()
    config = load_alert_config()
    run = get_run(evolution, run_id)
    
    alerts = check_thresholds(run, config)
    append_alerts(run, alerts, config)
    
    if alerts:
        print(f"ALERTS: {len(alerts)} alert(s) detected for {run['run_id']}")
        for a in alerts:
            print(f"  - {a['severity'].upper()}: {a['metric']} {a['condition']} {a['threshold']}")
        
        publish_blocker_event(run, alerts)
    else:
        print(f"OK: No alerts for {run['run_id']}")
    
    sys.exit(0)

if __name__ == "__main__":
    main()

