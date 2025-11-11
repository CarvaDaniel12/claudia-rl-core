#!/usr/bin/env python3
"""
Team Orchestrator - Distribui tarefas e monitora progresso
Uso: python scripts/orchestrate_team.py <comando>
"""
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

WORKSPACES = {
    "tech-lead": "C:/Users/User/Desktop/claudia",
    "analyst-pm": "C:/Users/User/Desktop/claudia-agent2",
    "architect-dev-helper": "C:/Users/User/Desktop/claudia-agent3",
    "dev-qa": "C:/Users/User/Desktop/claudia-agent4"
}

def assign_task(workspace, role, task_description, module):
    """Atribui tarefa a um workspace específico"""
    task = {
        "assigned_to": role,
        "task": task_description,
        "module": module,
        "status": "pending",
        "assigned_at": datetime.now(timezone.utc).isoformat(),
        "workspace": workspace
    }
    
    task_file = Path(WORKSPACES[workspace]) / "TASK.json"
    with task_file.open("w", encoding="utf-8") as f:
        json.dump(task, f, indent=2)
    
    print(f"[OK] Tarefa atribuída a {role} (workspace: {workspace})")
    print(f"     Módulo: {module}")
    print(f"     Tarefa: {task_description}")
    
    return task_file

def check_progress():
    """Verifica progresso de todos os workspaces"""
    print("\n=== STATUS DOS WORKSPACES ===\n")
    
    for ws_name, ws_path in WORKSPACES.items():
        task_file = Path(ws_path) / "TASK.json"
        
        if not task_file.exists():
            print(f"[{ws_name}]: SEM TAREFA")
            continue
        
        with task_file.open("r", encoding="utf-8") as f:
            task = json.load(f)
        
        status_icon = {
            "pending": "⏸️",
            "in_progress": "🔄",
            "completed": "✅",
            "blocked": "🚫"
        }.get(task.get("status"), "❓")
        
        print(f"[{ws_name}]: {status_icon} {task.get('status', 'unknown').upper()}")
        print(f"  Role: {task.get('assigned_to')}")
        print(f"  Task: {task.get('task')}")
        print(f"  Module: {task.get('module')}")
        if task.get("status") == "completed":
            print(f"  Output: {task.get('output_file', 'N/A')}")
        print()

def sync_branches():
    """Sync branches para consolidar trabalho"""
    print("\n=== SYNCING BRANCHES ===\n")
    
    for ws_name, ws_path in WORKSPACES.items():
        if ws_name == "tech-lead":
            continue
        
        print(f"[{ws_name}] Pulling latest...")
        subprocess.run(["git", "-C", ws_path, "pull", "origin", "master"], 
                      capture_output=True)
    
    print("[OK] All workspaces synced")

def create_chat_task_file(role, task, module, tab_number):
    """Cria arquivo de tarefa para aba de chat específica"""
    task_data = {
        "tab": tab_number,
        "role": role,
        "task": task,
        "module": module,
        "status": "pending",
        "context_pack": f"contracts/context_packs/{role.lower().replace('/', '_').replace(' ', '_')}.json",
        "assigned_at": datetime.now(timezone.utc).isoformat()
    }
    
    task_file = Path(f"TASK_TAB{tab_number}.json")
    with task_file.open("w", encoding="utf-8") as f:
        json.dump(task_data, f, indent=2)
    
    print(f"[OK] Tarefa para {role} (Tab {tab_number}) criada")
    print(f"     Arquivo: TASK_TAB{tab_number}.json")
    print(f"     Context Pack: {task_data['context_pack']}")
    
    return task_file

def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  WORKTREES MODE:")
        print("    python scripts/orchestrate_team.py assign <workspace> <role> <task> <module>")
        print("    python scripts/orchestrate_team.py status")
        print("    python scripts/orchestrate_team.py sync")
        print("")
        print("  CHAT TABS MODE:")
        print("    python scripts/orchestrate_team.py assign-tab <tab_num> <role> <task> <module>")
        print("    python scripts/orchestrate_team.py list-tabs")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "assign" and len(sys.argv) >= 6:
        assign_task(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif command == "assign-tab" and len(sys.argv) >= 6:
        create_chat_task_file(sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[2]))
    elif command == "list-tabs":
        for i in range(1, 9):
            task_file = Path(f"TASK_TAB{i}.json")
            if task_file.exists():
                with task_file.open() as f:
                    task = json.load(f)
                print(f"[Tab {i}] {task['role']}: {task['task']} ({task['status']})")
    elif command == "status":
        check_progress()
    elif command == "sync":
        sync_branches()
    else:
        print("ERROR: Comando inválido")
        sys.exit(1)

if __name__ == "__main__":
    main()

