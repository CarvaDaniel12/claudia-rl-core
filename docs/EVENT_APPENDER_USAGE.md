# Event Appender - Guia de Uso

## Instalação de Dependência

Antes de usar, instale a biblioteca `jsonschema`:

```bash
python -m pip install jsonschema
```

---

## Uso Básico

```bash
python scripts/append_event.py <TYPE> <ACTOR> <PAYLOAD_JSON_PATH> [<TIMESTAMP_ISO>]
```

**Parâmetros:**
- `TYPE`: Tipo do evento (deve existir no schema: SPEC_READY, DEV_DONE, QA_REPORT_READY, METRICS_UPDATED, etc.)
- `ACTOR`: Nome do agente que gerou o evento (Tech-Lead, Analyst/PM, Dev, QA/TEA, Data-Specialist, etc.)
- `PAYLOAD_JSON_PATH`: Caminho para arquivo JSON com payload do evento
- `TIMESTAMP_ISO` (opcional): Timestamp ISO 8601. Se omitido, usa timestamp atual.

---

## Exemplos de Uso

### 1. SPEC_READY (Analyst/PM → Architect + Dev)

**Quando:** Quick Spec aprovado e pronto para tech-spec

```bash
python scripts/append_event.py SPEC_READY "Analyst/PM" payloads/spec_ready.analytics.json
```

**Payload:** `payloads/spec_ready.analytics.json`
```json
{
  "module": "analytics",
  "spec_path": "docs/analytics_spec.md"
}
```

**Efeito:**
- Adiciona evento ao `contracts/events.jsonl`
- Registra linha em `SESSION_LOG.md`
- Sinaliza Architect e Dev para iniciar tech-spec

---

### 2. DEV_DONE (Dev → QA/TEA)

**Quando:** Implementação concluída nos paths permitidos

```bash
python scripts/append_event.py DEV_DONE "Dev" payloads/dev_done.analytics.json
```

**Payload:** `payloads/dev_done.analytics.json`
```json
{
  "module": "analytics",
  "artifacts": [
    "contracts/analytics_plan.json",
    "docs/analytics_impl.md"
  ]
}
```

**Efeito:**
- Adiciona evento ao `contracts/events.jsonl`
- Registra linha em `SESSION_LOG.md`
- **Aciona automaticamente** QA/TEA para iniciar testes

---

### 3. QA_REPORT_READY (QA/TEA → Tech-Lead + Data-Specialist)

**Quando:** Avaliação completa com relatório de qualidade

```bash
python scripts/append_event.py QA_REPORT_READY "QA/TEA" payloads/qa_ready.analytics.json
```

**Payload:** `payloads/qa_ready.analytics.json`
```json
{
  "module": "analytics",
  "pass_rate": 0.85,
  "blockers": [],
  "report": "reports/analytics_qa.md"
}
```

**Efeito:**
- Adiciona evento ao `contracts/events.jsonl`
- Registra linha em `SESSION_LOG.md`
- Notifica Tech-Lead (decisão DoD) e Data-Specialist (métricas)

---

### 4. METRICS_UPDATED (Data-Specialist → Tech-Lead + Reward-Tuner)

**Quando:** Métricas consolidadas e evolutionário atualizado

```bash
python scripts/append_event.py METRICS_UPDATED "Data-Specialist" payloads/metrics_updated.analytics.json
```

**Payload:** `payloads/metrics_updated.analytics.json`
```json
{
  "run_id": "run_001",
  "reward": 0.72,
  "pass_rate": 0.85,
  "duration_s": 120
}
```

**Efeito:**
- Adiciona evento ao `contracts/events.jsonl`
- Registra linha em `SESSION_LOG.md`
- Notifica Tech-Lead (decisões) e Reward-Tuner (ajustes de α,β,γ,δ)

---

## Validação Automática

O script valida automaticamente:
1. **Existência do payload**: Arquivo JSON deve existir
2. **Schema compliance**: Evento deve seguir `contracts/events.schema.json`
3. **Atomicidade**: Usa lockfile para evitar race conditions

**Se houver erro:**
- Exit code 1: Argumentos inválidos
- Exit code 2: Validação de schema falhou ou jsonschema não instalado
- Exit code 3: Lockfile busy (timeout)

---

## Leitura de Eventos

Para ler todos os eventos:

```bash
cat contracts/events.jsonl
```

Para filtrar eventos por tipo:

```bash
# Windows (PowerShell)
Select-String -Path contracts/events.jsonl -Pattern "SPEC_READY"

# Linux/Mac
grep "SPEC_READY" contracts/events.jsonl
```

Para analisar eventos em Python:

```python
import json
from pathlib import Path

events = []
with Path("contracts/events.jsonl").open("r", encoding="utf-8") as f:
    for line in f:
        events.append(json.loads(line))

# Filtrar por tipo
spec_ready_events = [e for e in events if e["type"] == "SPEC_READY"]
print(f"Total SPEC_READY: {len(spec_ready_events)}")
```

---

## Criar Payloads Customizados

Para criar um payload para outro módulo (ex: `fees_taxes`):

```json
# payloads/spec_ready.fees_taxes.json
{
  "module": "fees_taxes",
  "spec_path": "docs/fees_taxes_spec.md"
}
```

Depois executar:

```bash
python scripts/append_event.py SPEC_READY "Analyst/PM" payloads/spec_ready.fees_taxes.json
```

---

## Troubleshooting

### Erro: `jsonschema not installed`

```bash
python -m pip install jsonschema
```

### Erro: `lockfile busy`

O script esperou 5 segundos e o lockfile ainda existe. Remover manualmente:

```bash
rm contracts/.events.lock
```

### Erro: `schema validation failed`

Verifique se o payload está aderente ao schema. Exemplo de evento inválido:

```json
{
  "type": "INVALID_TYPE",  // Tipo não existe no enum do schema
  "actor": "Unknown"       // Actor não está no enum
}
```

---

**Versão**: 1.0  
**Última Atualização**: 2025-11-10

