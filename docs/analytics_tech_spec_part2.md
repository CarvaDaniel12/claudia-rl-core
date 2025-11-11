# Tech-Spec: Analytics Module (Parte 2)

**Continuação de**: docs/analytics_tech_spec.md

---

## Estratégia de Deploy

### Fase 1: Preparação (Schemas)
1. Criar `contracts/run_data_schema.json`
2. Criar `contracts/alert_config.json`
3. Validar schemas com jsonschema

### Fase 2: Storage
4. Criar `rl_atomic/` directory
5. Criar `rl_atomic/evolution.json` vazio:
```json
{
  "schema_version": "1.0",
  "runs": []
}
```

### Fase 3: Scripts
6. Implementar `scripts/aggregate_metrics.py` (< 200 linhas)
7. Implementar `scripts/generate_snapshot.py` (< 150 linhas)
8. Implementar `scripts/detect_alerts.py` (< 150 linhas)

### Fase 4: Integração
9. QA/TEA testa com dados de mock (2 cenários do spec)
10. Integrar com event bus (append_event.py para METRICS_UPDATED)
11. Data-Specialist valida com run real

---

## Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **evolution.json > 10MB** | Médio | Alto | Rotação mensal: mover runs antigos para `rl_atomic/archive/YYYY-MM.json` |
| **Race conditions** | Baixo | Alto | Lockfile atômico (já usado em append_event.py) |
| **Schema drift** | Baixo | Médio | Versionamento de schema (`schema_version` field) + script de migração |
| **Backup failure** | Baixo | Alto | Validar backup completo antes de delete; manter últimos 3 backups |
| **Disk full** | Muito Baixo | Crítico | Monitorar espaço em disco; alerta se < 1GB disponível |

---

## Migração de Schema (Futuro)

Se schema mudar de v1.0 para v2.0:

```python
# scripts/migrate_evolution.py
def migrate_v1_to_v2(evolution):
    if evolution["schema_version"] != "1.0":
        return evolution  # já migrado
    
    # Adicionar novos campos com defaults
    for run in evolution["runs"]:
        run.setdefault("new_field", default_value)
    
    evolution["schema_version"] = "2.0"
    return evolution
```

---

## Monitoramento

### Métricas a Rastrear
- Taxa de sucesso de agregação (< 99.9% → alerta)
- Tempo de agregação (> 5s → alerta)
- Tamanho de evolution.json (> 8MB → rotacionar)
- Alertas críticos não resolvidos (> 2 → escalar)

### Logs
- `logs/analytics.log` (INFO/WARNING/ERROR)
- Rotação diária, manter últimos 7 dias

---

## Backup e Recuperação

### Backup Automático
```python
# Antes de cada write em evolution.json:
backup_path = f"rl_atomic/backups/evolution_{timestamp}.json"
shutil.copy("rl_atomic/evolution.json", backup_path)
# Manter últimos 3 backups, deletar mais antigos
```

### Recuperação
```python
# Se evolution.json corrompido:
latest_backup = find_latest_backup("rl_atomic/backups/")
shutil.copy(latest_backup, "rl_atomic/evolution.json")
log.error(f"Recovered from backup: {latest_backup}")
```

---

## Testing Strategy (para QA/TEA)

### Testes Unitários
1. Schema validation (jsonschema)
2. Aggregate append (count verification)
3. Snapshot generation (output format)
4. Alert detection (threshold logic)

### Testes de Integração
5. End-to-end: run_data.json → evolution.json → snapshot.md → event
6. Concorrência: múltiplos appends simultâneos (lockfile test)
7. Error handling: schema invalid, file missing, disk full

### Testes de Performance
8. Aggregate 1000 runs (< 5s target)
9. Generate snapshot from 1000 runs (< 3s target)
10. Detect alerts from 1000 runs (< 2s target)

---

## Next Steps (Implementação)

1. **Dev** cria schemas em `contracts/`:
   - `run_data_schema.json`
   - `alert_config.json`

2. **Dev** implementa scripts em `scripts/`:
   - `aggregate_metrics.py` (≤ 200 linhas)
   - `generate_snapshot.py` (≤ 150 linhas)
   - `detect_alerts.py` (≤ 150 linhas)

3. **Dev** cria documentação:
   - `docs/analytics_impl.md` (como usar cada script)

4. **Dev** publica `DEV_DONE` event

5. **QA/TEA** valida com asserts mínimos + dados de mock

6. **Data-Specialist** integra com workflow real de runs

---

**Aprovado por**: Tech-Lead  
**Data**: 2025-11-10

