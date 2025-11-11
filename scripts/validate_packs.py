#!/usr/bin/env python3
"""
Validate Context Packs - Detecta packs desatualizados ou inválidos
Uso: python scripts/validate_packs.py
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

PACKS_DIR = Path("contracts/context_packs")
MAX_AGE_DAYS = 7

def validate_pack(pack_path):
    """Valida um pack individual"""
    errors = []
    warnings = []
    
    try:
        with pack_path.open("r", encoding="utf-8") as f:
            pack = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"JSON inválido: {e}")
        return errors, warnings
    
    # Check 1: Campos obrigatórios
    is_global = pack.get("type") == "global"
    required_fields = ["generated_at", "project", "description"]
    if not is_global:
        required_fields.append("role")
    
    for field in required_fields:
        if field not in pack:
            errors.append(f"Campo obrigatório ausente: {field}")
    
    # Check 2: Timestamp
    if "generated_at" in pack:
        try:
            generated_at = datetime.fromisoformat(pack["generated_at"].replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - generated_at
            age_days = age.days
            
            if age_days > MAX_AGE_DAYS:
                warnings.append(f"Pack desatualizado: {age_days} dias (limite: {MAX_AGE_DAYS})")
        except ValueError:
            errors.append("Timestamp inválido (formato deve ser ISO 8601)")
    
    # Check 3: Paths existem?
    if "specialization" in pack and "primary_paths" in pack["specialization"]:
        for path_pattern in pack["specialization"]["primary_paths"]:
            # Não validar globs, apenas avisar se paths específicos não existem
            if "*" not in path_pattern:
                if not Path(path_pattern).exists():
                    warnings.append(f"Path não encontrado: {path_pattern}")
    
    return errors, warnings

def validate_all():
    """Valida todos os packs"""
    if not PACKS_DIR.exists():
        print("ERROR: Diretório contracts/context_packs/ não encontrado", file=sys.stderr)
        sys.exit(1)
    
    packs = list(PACKS_DIR.glob("*.json"))
    if not packs:
        print("WARNING: Nenhum pack encontrado", file=sys.stderr)
        sys.exit(0)
    
    total_errors = 0
    total_warnings = 0
    
    print(f"Validando {len(packs)} pack(s)...\n")
    
    for pack_path in sorted(packs):
        print(f"[PACK] {pack_path.name}")
        errors, warnings = validate_pack(pack_path)
        
        if errors:
            total_errors += len(errors)
            for err in errors:
                print(f"  [ERROR] {err}")
        
        if warnings:
            total_warnings += len(warnings)
            for warn in warnings:
                print(f"  [WARNING] {warn}")
        
        if not errors and not warnings:
            print("  [OK]")
        
        print()
    
    print(f"Resumo: {total_errors} erro(s), {total_warnings} aviso(s)")
    
    if total_errors > 0:
        sys.exit(1)
    elif total_warnings > 0:
        sys.exit(0)  # Warnings não falham CI
    else:
        sys.exit(0)

if __name__ == "__main__":
    validate_all()


