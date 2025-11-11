#!/usr/bin/env python3
"""
Generate Snapshot - Gera relatorio de metricas em markdown
Uso: python scripts/generate_snapshot.py
Saida: reports/metrics_snapshot.md
"""
import json
import sys
from pathlib import Path
from statistics import mean, median
from datetime import datetime

EVOLUTION_PATH = Path("rl_atomic/evolution.json")
SNAPSHOT_PATH = Path("reports/metrics_snapshot.md")

def load_evolution():
    """Carrega evolution.json"""
    if not EVOLUTION_PATH.exists():
        print("ERROR: evolution.json not found", file=sys.stderr)
        sys.exit(1)
    
    with EVOLUTION_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def get_last_n_runs(evolution, n=5):
    """Retorna ultimos N runs"""
    return evolution["runs"][-n:]

def calculate_trend(values):
    """Calcula tendencia (positiva, negativa, estavel)"""
    if len(values) < 2:
        return "stable", 0
    
    first_half = mean(values[:len(values)//2])
    second_half = mean(values[len(values)//2:])
    delta = second_half - first_half
    
    if abs(delta) < 0.02:
        return "stable", 0
    elif delta > 0:
        return "up", delta
    else:
        return "down", delta

def format_trend(trend, delta):
    """Formata indicador de tendencia"""
    if trend == "up":
        return f"+{delta:.1%}"
    elif trend == "down":
        return f"{delta:.1%}"
    else:
        return "~"

def generate_snapshot(evolution):
    """Gera snapshot de metricas"""
    runs = evolution["runs"]
    if not runs:
        return "# Metrics Snapshot\n\nNo runs available.\n"
    
    last = runs[-1]
    recent = get_last_n_runs(evolution, 5)
    
    output = []
    output.append(f"# Metrics Snapshot - Run {last['run_id']}\n")
    output.append(f"**Generated**: {datetime.now().isoformat()}\n")
    output.append(f"**Total Runs**: {len(runs)}\n")
    output.append("\n---\n")
    
    output.append("\n## Ultimo Run\n")
    output.append(f"- **Run ID**: {last['run_id']}\n")
    output.append(f"- **Timestamp**: {last['timestamp']}\n")
    output.append(f"- **Pass Rate**: {last['assertions_pass_rate']:.1%}\n")
    output.append(f"- **Reward**: {last['reward']:.2f}\n")
    output.append(f"- **Coverage**: {last['coverage']:.1%}\n")
    output.append(f"- **Duration**: {last['duration_s']}s\n")
    output.append(f"- **Selector Success**: {last['selector_success_rate']:.1%}\n")
    
    output.append("\n---\n")
    output.append("\n## Tendencias (Ultimos 5 Runs)\n\n")
    
    if len(recent) >= 2:
        metrics = {
            "Pass Rate": [r["assertions_pass_rate"] for r in recent],
            "Reward": [r["reward"] for r in recent],
            "Coverage": [r["coverage"] for r in recent],
            "Duration (s)": [r["duration_s"] for r in recent],
            "Selector Success": [r["selector_success_rate"] for r in recent]
        }
        
        output.append("| Metrica | Media | Mediana | P90 | Tendencia |\n")
        output.append("|---------|-------|---------|-----|----------|\n")
        
        for name, values in metrics.items():
            avg = mean(values)
            med = median(values)
            p90 = sorted(values)[int(len(values) * 0.9)] if len(values) > 1 else values[0]
            trend, delta = calculate_trend(values)
            trend_str = format_trend(trend, delta)
            
            if name in ["Pass Rate", "Coverage", "Selector Success"]:
                output.append(f"| {name} | {avg:.1%} | {med:.1%} | {p90:.1%} | {trend_str} |\n")
            elif name == "Reward":
                output.append(f"| {name} | {avg:.2f} | {med:.2f} | {p90:.2f} | {trend_str} |\n")
            else:
                output.append(f"| {name} | {avg:.0f} | {med:.0f} | {p90:.0f} | {trend_str} |\n")
    else:
        output.append("*Necessario pelo menos 2 runs para calcular tendencias*\n")
    
    output.append("\n---\n")
    output.append("\n## Historico Recente\n\n")
    output.append("| Run ID | Timestamp | Pass Rate | Reward | Coverage |\n")
    output.append("|--------|-----------|-----------|--------|----------|\n")
    
    for r in reversed(recent):
        output.append(f"| {r['run_id']} | {r['timestamp'][:19]} | ")
        output.append(f"{r['assertions_pass_rate']:.1%} | {r['reward']:.2f} | ")
        output.append(f"{r['coverage']:.1%} |\n")
    
    return "".join(output)

def main():
    evolution = load_evolution()
    snapshot = generate_snapshot(evolution)
    
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SNAPSHOT_PATH.open("w", encoding="utf-8") as f:
        f.write(snapshot)
    
    print(f"OK: Snapshot generated at {SNAPSHOT_PATH}")
    sys.exit(0)

if __name__ == "__main__":
    main()

