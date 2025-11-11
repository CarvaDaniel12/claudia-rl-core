# Tech-Spec: Analytics Module

**Módulo**: analytics  
**Versão**: 1.0  
**Data**: 2025-11-10  
**Autor**: Architect  
**Baseado em**: docs/analytics_spec.md

---

## Arquitetura de Componentes

```
┌─────────────────┐
│   QA/TEA        │ (entrada: run_data.json)
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Analytics      │ (processamento)
│  - validate     │
│  - aggregate    │
│  - alert        │
└────────┬────────┘
         │
         ├─> rl_atomic/evolution.json (append-only)
         ├─> reports/metrics_snapshot.md
         ├─> reports/alerts.md
         └─> METRICS_UPDATED event
```

---

## Interfaces (Contratos JSON)

### 1. Entrada: Run Data Schema

**Arquivo**: `contracts/run_data_schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Run Data Schema",
  "type": "object",
  "required": ["run_id", "timestamp", "assertions_pass_rate", "selector_success_rate", "reward", "duration_s", "coverage"],
  "properties": {
    "run_id": {"type": "string", "pattern": "^run_\\d{3,}$"},
    "timestamp": {"type": "string", "format": "date-time"},
    "assertions_pass_rate": {"type": "number", "minimum": 0, "maximum": 1},
    "selector_success_rate": {"type": "number", "minimum": 0, "maximum": 1},
    "reward": {"type": "number", "minimum": -1, "maximum": 1},
    "duration_s": {"type": "integer", "minimum": 1},
    "coverage": {"type": "number", "minimum": 0, "maximum": 1}
  }
}
```

### 2. Saída: Evolution JSON

**Arquivo**: `rl_atomic/evolution.json`

```json
{
  "schema_version": "1.0",
  "runs": [
    {
      "run_id": "run_001",
      "timestamp": "2025-11-10T18:00:00Z",
      "assertions_pass_rate": 0.92,
      "selector_success_rate": 0.95,
      "reward": 0.78,
      "duration_s": 85,
      "coverage": 0.65
    }
  ]
}
```

### 3. Configuração: Alert Config

**Arquivo**: `contracts/alert_config.json`

```json
{
  "thresholds": {
    "pass_rate_min": 0.70,
    "reward_min": 0.50,
    "coverage_growth_min": 0.02,
    "duration_max": 300
  },
  "severities": {
    "critical": ["pass_rate_min", "reward_min"],
    "warning": ["coverage_growth_min", "duration_max"]
  }
}
```

---

## Fluxos Detalhados

### Fluxo 1: Agregar Métricas de Run

**Script**: `scripts/aggregate_metrics.py`

```python
# Pseudocódigo
1. Ler run_data.json (entrada)
2. Validar contra run_data_schema.json
3. Ler rl_atomic/evolution.json (lock)
4. Append novo run ao array "runs"
5. Salvar rl_atomic/evolution.json (unlock)
6. Publicar METRICS_UPDATED event
```

**Selectors/Observability** (N/A - backend script)

**Waits Semânticos** (N/A - não UI)

**Tratamento de Erros**:
- Se schema inválido → log error + skip (não crashar)
- Se evolution.json corrompido → backup + recreate
- Se lockfile stuck > 10s → abort + alerta

---

### Fluxo 2: Gerar Snapshot

**Script**: `scripts/generate_snapshot.py`

```python
# Pseudocódigo
1. Ler rl_atomic/evolution.json
2. Extrair último run
3. Calcular agregações (últimos 5 runs):
   - Média pass_rate
   - Média reward
   - Tendência coverage (delta)
4. Gerar tabela markdown
5. Salvar reports/metrics_snapshot.md
```

**Output Format** (reports/metrics_snapshot.md):

```markdown
# Metrics Snapshot - Run run_042

## Último Run
- **Run ID**: run_042
- **Timestamp**: 2025-11-10T19:00:00Z
- **Pass Rate**: 85% ✓
- **Reward**: 0.72 ✓
- **Coverage**: 65%
- **Duration**: 120s

## Tendências (Últimos 5 Runs)
| Métrica | Média | P50 | P90 | Tendência |
|---------|-------|-----|-----|-----------|
| Pass Rate | 82% | 85% | 90% | ↗️ +3% |
| Reward | 0.68 | 0.72 | 0.80 | ↗️ +5% |
| Coverage | 62% | 65% | 68% | ↗️ +2% |
```

---

### Fluxo 3: Detectar Alertas

**Script**: `scripts/detect_alerts.py`

```python
# Pseudocódigo
1. Ler último run de rl_atomic/evolution.json
2. Ler thresholds de contracts/alert_config.json
3. Comparar métricas com thresholds:
   - pass_rate < 0.70 → CRITICAL
   - reward < 0.50 → CRITICAL
   - coverage delta < 0.02 (5 runs) → WARNING
   - duration > 300s → WARNING
4. Se alerta detectado:
   - Append em reports/alerts.md
   - Publicar BLOCKER_RAISED (se CRITICAL)
```

---

## Testabilidade (QA/TEA Integration)

### Asserts Mínimos

**Assert 1: Schema Validation**
```python
run_data = load_json("run_data.json")
validate(run_data, schema="contracts/run_data_schema.json")
assert validate.success == True
```

**Assert 2: Evolution Append**
```python
initial_count = len(evolution["runs"])
aggregate_metrics("run_data.json")
final_count = len(evolution["runs"])
assert final_count == initial_count + 1
```

**Assert 3: Snapshot Generation**
```python
generate_snapshot()
assert Path("reports/metrics_snapshot.md").exists()
assert "## Último Run" in read_file("reports/metrics_snapshot.md")
```

**Assert 4: Alert Detection**
```python
# Simular run com pass_rate baixo
run_data = {"pass_rate": 0.62, ...}
detect_alerts(run_data)
assert Path("reports/alerts.md").read_text().contains("CRITICAL")
```

### Waits Semânticos (N/A)

Este módulo é backend (scripts Python), não há UI/DOM para testar com Playwright.

### Selectors Estáveis (N/A)

Backend module - sem interação com DOM.

---

## Tratamento de Erros

| Erro | Causa | Tratamento |
|------|-------|------------|
| Schema Invalid | run_data.json não conforme | Log error + skip run (não crashar) |
| File Not Found | evolution.json ausente | Criar novo com schema_version |
| Lock Timeout | Processo anterior travou | Remover lock + retry (max 3x) |
| JSON Corrupt | Parse error em evolution.json | Backup corrupted + recreate from backup |
| Disk Full | Sem espaço para write | Alert CRITICAL + abort |

---

## Performance

### Targets
- **Agregar métricas**: < 5s (até 1000 runs)
- **Gerar snapshot**: < 3s
- **Detectar alertas**: < 2s

### Otimizações
1. **Append-only** em evolution.json (não reescrever array inteiro)
2. **Lockfile** com timeout (evitar deadlocks)
3. **Rolling window** para agregações (últimos 5-20 runs, não todos)
4. **Lazy load** de JSON (streamed read para arrays grandes)

---

## Dependências

### Python Libs
- `json` (stdlib)
- `jsonschema` (já instalado)
- `pathlib` (stdlib)
- `statistics` (stdlib)
- `datetime` (stdlib)

### Arquivos Externos
- `contracts/run_data_schema.json`
- `contracts/alert_config.json`
- `rl_atomic/evolution.json` (criado se ausente)
- `scripts/append_event.py` (para METRICS_UPDATED)

---

## Continuação

Para estratégia de deploy, riscos técnicos e próximos passos, ver:
**docs/analytics_tech_spec_part2.md**

---

**Aprovado por**: Tech-Lead  
**Próximo passo**: Implementação (Dev)

