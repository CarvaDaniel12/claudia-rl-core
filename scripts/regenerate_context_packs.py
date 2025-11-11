#!/usr/bin/env python3
"""
Regenerate Context Packs - Gera packs por papel após index update
Uso: python scripts/regenerate_context_packs.py [--role ROLE]
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

PACKS_DIR = Path("contracts/context_packs")
ROLES = {
    "tech-lead": {
        "description": "Orquestra time, aplica guardrails, valida DoR/DoD",
        "primary_paths": ["docs/*.md", "contracts/*.json", "SESSION_LOG.md"],
        "keywords": ["orchestration", "dor", "dod", "guardrails", "handoff"],
        "mcp_hints": "decision making, team coordination"
    },
    "analyst_pm": {
        "description": "PRD/Quick Spec, critérios de aceitação, backlog",
        "primary_paths": ["docs/*_spec.md", "contracts/acceptance_criteria.json"],
        "keywords": ["requirements", "user stories", "acceptance", "backlog"],
        "mcp_hints": "product requirements, specifications"
    },
    "architect": {
        "description": "Tech-spec, arquitetura, interfaces, testabilidade",
        "primary_paths": ["docs/*_tech_spec.md", "contracts/*_interface.json"],
        "keywords": ["architecture", "interfaces", "design", "testability"],
        "mcp_hints": "system design, technical architecture"
    },
    "dev": {
        "description": "Implementação em paths permitidos",
        "primary_paths": ["contracts/*_plan.json", "docs/*_impl.md", "scripts/*.py"],
        "keywords": ["implementation", "coding", "testing", "integration"],
        "mcp_hints": "code implementation, development"
    },
    "qa_tea": {
        "description": "Test Architect: asserts, waits semânticos, relatórios",
        "primary_paths": ["reports/*_qa.md", "docs/test_strategy.md", "docs/stabilizer_notes.md"],
        "keywords": ["testing", "assertions", "waits", "quality", "flake"],
        "mcp_hints": "test architecture, quality assurance"
    },
    "data_specialist": {
        "description": "Métricas, evolução temporal, alertas",
        "primary_paths": ["rl_atomic/evolution.json", "reports/metrics_snapshot.md", "reports/alerts.md"],
        "keywords": ["metrics", "analytics", "trends", "alerts", "observability"],
        "mcp_hints": "data analysis, metrics tracking"
    },
    "reward_tuner": {
        "description": "Calibra A→D, ablação experimental",
        "primary_paths": ["contracts/reward_profile.json", "docs/rl_ablation.md"],
        "keywords": ["reward", "reinforcement", "tuning", "ablation", "optimization"],
        "mcp_hints": "reward engineering, RL optimization"
    },
    "coverage_mapper": {
        "description": "Mapa de cobertura, gap analysis, alvos de exploração",
        "primary_paths": ["reports/coverage_map.md", "docs/exploration_targets.md"],
        "keywords": ["coverage", "gaps", "exploration", "affordances", "routes"],
        "mcp_hints": "coverage analysis, exploration planning"
    }
}

GLOBAL_REFS = [
    "docs/TEAM_OPERATING_AGREEMENT.md",
    "contracts/diff_policy.json",
    "contracts/run_data_schema.json",
    "contracts/reward_profile.json"
]

def generate_pack(role, config):
    """Gera pack JSON para um papel específico"""
    pack = {
        "role": role,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "spark",
        "description": config["description"],
        
        "identity_reminder": f"VOCE EH O {role.upper().replace('-', ' ')}. {config['description']}",
        
        "global_refs": {
            "team_agreement": "docs/TEAM_OPERATING_AGREEMENT.md",
            "diff_policy": "contracts/diff_policy.json",
            "run_schema": "contracts/run_data_schema.json",
            "reward_profile": "contracts/reward_profile.json"
        },
        
        "specialization": {
            "primary_paths": config["primary_paths"],
            "keywords": config["keywords"],
            "mcp_hints": config["mcp_hints"]
        },
        
        "mcp_usage": {
            "search_example": f"search_repo(query='{config['mcp_hints']}', top_k=6, intent='impl')",
            "file_context_example": "file_context(symbol_or_path='src/...:functionName', context_lines=20)"
        },
        
        "anti_amnesia": {
            "enabled": True,
            "reminder": f"Voce eh responsavel por: {config['description']}",
            "frequency": "every_5_messages"
        }
    }
    
    return pack

def generate_global_pack():
    """Gera pack global (incluído em todos)"""
    return {
        "type": "global",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "spark",
        "description": "Referencias globais para todos os agentes",
        
        "refs": GLOBAL_REFS,
        
        "guardrails": {
            "allowed_writes": [
                "docs/*.md",
                "contracts/*.json",
                "reports/*.md",
                "scripts/*.py",
                "AGENT_CONTEXT.json",
                "SESSION_LOG.md"
            ],
            "diff_limits": {
                "docs": 1200,
                "reports": 800,
                "contracts": 400,
                "scripts": 200
            }
        },
        
        "project_structure": {
            "total_files": 248,
            "size_mb": 12.5,
            "primary_languages": ["TypeScript", "Python"],
            "last_indexed": datetime.now(timezone.utc).isoformat()
        }
    }

def regenerate_all():
    """Regenera todos os packs"""
    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Global pack
    global_pack = generate_global_pack()
    global_path = PACKS_DIR / "_global.json"
    with global_path.open("w", encoding="utf-8") as f:
        json.dump(global_pack, f, indent=2, ensure_ascii=False)
    print(f"[OK] _global.json gerado")
    
    # Role-specific packs
    for role, config in ROLES.items():
        pack = generate_pack(role, config)
        pack_path = PACKS_DIR / f"{role}.json"
        with pack_path.open("w", encoding="utf-8") as f:
            json.dump(pack, f, indent=2, ensure_ascii=False)
        print(f"[OK] {role}.json gerado")

def main():
    if "--role" in sys.argv:
        idx = sys.argv.index("--role")
        role = sys.argv[idx + 1]
        if role not in ROLES:
            print(f"ERROR: Role '{role}' desconhecido", file=sys.stderr)
            sys.exit(1)
        config = ROLES[role]
        pack = generate_pack(role, config)
        pack_path = PACKS_DIR / f"{role}.json"
        PACKS_DIR.mkdir(parents=True, exist_ok=True)
        with pack_path.open("w", encoding="utf-8") as f:
            json.dump(pack, f, indent=2, ensure_ascii=False)
        print(f"[OK] {role}.json atualizado")
    else:
        regenerate_all()
    
    sys.exit(0)

if __name__ == "__main__":
    main()


