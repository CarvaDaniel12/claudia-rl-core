# Workflow Guide - Time RL Core

## Visão Geral

Este guia documenta como usar o **time RL Core** com 8 agentes especializados para desenvolvimento de sistemas RL Atômico.

---

## 🚀 Quick Start

### 1. Iniciar Party Mode com Team RL Core

```bash
# Navegar para o diretório do projeto
cd C:\Users\User\Desktop\claudia

# Iniciar party mode com o time customizado
npx bmad-method@alpha party-mode --team team-rl-core
```

**Ou usando workflow específico:**

```bash
# Iniciar workflow de party-mode do BMM
npx bmad-method@alpha workflow bmm/party-mode --team team-rl-core
```

---

## 📋 Ciclo Completo de Desenvolvimento

### Fase 1: SPEC_READY (Analyst/PM → Architect + Dev)

**1.1. Analyst/PM cria Quick Spec**

```bash
# Usar workflow de Quick Spec
npx bmad-method@alpha workflow bmm/quick-spec-flow --module analytics
```

O Analyst/PM produz:
- `docs/analytics_spec.md` (Quick Spec ≤ 200 linhas)
- `contracts/acceptance_criteria.json` (Critérios testáveis)

**1.2. Analyst/PM publica SPEC_READY**

Adicionar ao `contracts/events.jsonl`:
```json
{"type":"SPEC_READY","timestamp":"2025-11-10T10:00:00Z","actor":"Analyst/PM","payload":{"module":"analytics","spec_path":"docs/analytics_spec.md"}}
```

**1.3. Tech-Lead valida DoR**

Checklist:
- [ ] Quick Spec aprovado
- [ ] Critérios testáveis
- [ ] Pontos de integração mapeados
- [ ] Dados de teste definidos

Se OK, Tech-Lead publica `DOR_VALIDATED` e sinaliza Architect + Dev.

---

### Fase 2: Tech-Spec (Architect)

**2.1. Architect converte Spec → Tech-Spec**

```bash
# Usar workflow de Tech-Spec
npx bmad-method@alpha workflow bmm/tech-spec --module analytics
```

O Architect produz:
- `docs/analytics_tech_spec.md` (Arquitetura detalhada)
- `contracts/analytics_interface.json` (Contratos de API)
- `contracts/analytics_test_data.json` (Mocks e fixtures)

**2.2. Architect coordena com Dev e QA/TEA**

- Definir selectors estáveis (data-testid)
- Especificar waits semânticos
- Mapear affordances testáveis

---

### Fase 3: DEV_DONE (Dev → QA/TEA)

**3.1. Dev implementa nos paths permitidos**

```bash
# Usar workflow de implementação
npx bmad-method@alpha workflow bmm/dev-story --module analytics
```

O Dev produz:
- `contracts/analytics_plan.json` (Plano estruturado)
- `docs/analytics_impl.md` (Implementação documentada ≤ 200 linhas)
- `reports/analytics_dev_notes.md` (Decisões técnicas)

**3.2. Dev publica DEV_DONE**

Adicionar ao `contracts/events.jsonl`:
```json
{"type":"DEV_DONE","timestamp":"2025-11-10T12:00:00Z","actor":"Dev","payload":{"module":"analytics","artifacts":["contracts/analytics_plan.json","docs/analytics_impl.md"]}}
```

QA/TEA é **automaticamente acionado** pelo evento.

---

### Fase 4: QA_REPORT_READY (QA/TEA → Tech-Lead + Data-Specialist)

**4.1. QA/TEA executa avaliação**

```bash
# Usar workflow de Test Architecture
npx bmad-method@alpha workflow bmm/testarch/test-design --module analytics
```

O QA/TEA:
- Executa 1 run com asserts mínimos + waits semânticos
- Gera `reports/analytics_qa_report.md` com pass_rate e evidências
- Propõe heurísticas anti-flake em `docs/stabilizer_notes.md`

**4.2. QA/TEA publica QA_REPORT_READY**

Adicionar ao `contracts/events.jsonl`:
```json
{"type":"QA_REPORT_READY","timestamp":"2025-11-10T14:00:00Z","actor":"QA/TEA","payload":{"module":"analytics","pass_rate":0.85,"blockers":["selector-timeout-login"],"report":"reports/analytics_qa.md"}}
```

Se blockers críticos, também publicar `BLOCKER_RAISED`.

---

### Fase 5: METRICS_UPDATED (Data-Specialist → Tech-Lead + Reward-Tuner)

**5.1. Data-Specialist consolida métricas**

O Data-Specialist:
- Atualiza `rl_atomic/evolution.json` (via scripts externos)
- Gera `reports/metrics_snapshot.md` com tendências
- Detecta alertas (pass_rate < 70%, reward < 0.5, etc.)

**5.2. Data-Specialist publica METRICS_UPDATED**

Adicionar ao `contracts/events.jsonl`:
```json
{"type":"METRICS_UPDATED","timestamp":"2025-11-10T15:00:00Z","actor":"Data-Specialist","payload":{"run_id":"run_042","reward":0.72,"pass_rate":0.85,"duration_s":120}}
```

---

### Fase 6: Decisão do Tech-Lead

**6.1. Tech-Lead valida DoD**

Checklist:
- [ ] Artifacts nos paths corretos
- [ ] Diffs ≤ 200 linhas
- [ ] QA report gerado
- [ ] Métricas atualizadas
- [ ] Evidências reprodutíveis

**6.2. Tech-Lead decide:**

| Cenário | Ação |
|---------|------|
| DoD OK + Pass Rate ≥ 80% | ✅ Aprovar e fechar história |
| DoD OK + Pass Rate < 80% | 🔄 Iterar (Dev + QA/TEA) |
| Blockers críticos | 🚨 Escalar (Architect + PM) |
| Path violation | ⛔ Abortar e notificar ClaudIA |

**6.3. Tech-Lead publica DOD_VALIDATED**

```json
{"type":"DOD_VALIDATED","timestamp":"2025-11-10T16:00:00Z","actor":"Tech-Lead","payload":{"module":"analytics","status":"approved"}}
```

---

## 🔄 Ciclo Paralelo: Reward Tuning

### Reward-Tuner reage a METRICS_UPDATED

**1. Analisa trend do reward**

Se reward < 0.5 por 5 runs consecutivos:
- Aumentar α (assertion_weight) de 0.4 → 0.45
- Documentar em `reports/reward_changelog.md`

**2. Atualiza reward profile**

Editar `contracts/reward_profile.json`:
```json
{
  "α": 0.45,
  "β": 0.30,
  "γ": 0.20,
  "δ": 0.10,
  "ε": 0.15,
  "K": 0.95,
  "p": -0.5
}
```

**3. Publica REWARD_ADJUSTED**

```json
{"type":"REWARD_ADJUSTED","timestamp":"2025-11-10T15:30:00Z","actor":"Reward-Tuner","payload":{"profile":"contracts/reward_profile.json","reason":"Low reward trend","changes":{"α":0.45}}}
```

---

## 🗺️ Ciclo Paralelo: Coverage Mapping

### Coverage-Mapper atualiza mapa de cobertura

**1. Consolida playwright_knowledge.json**

Processar runs recentes e gerar:
- `reports/coverage_map.md` (% cobertura por módulo)
- `reports/coverage_gaps.md` (Top 10 lacunas)

**2. Prioriza alvos de exploração**

Selecionar 5 rotas alvo para próximo ciclo:
- `docs/exploration_targets.md`

**3. Publica COVERAGE_UPDATED**

```json
{"type":"COVERAGE_UPDATED","timestamp":"2025-11-10T15:45:00Z","actor":"Coverage-Mapper","payload":{"coverage_pct":0.65,"top_gaps":["route1","route2"],"targets":["target1","target2"]}}
```

---

## 📂 Estrutura de Arquivos (Paths Permitidos)

```
claudia/
├── AGENT_CONTEXT.json          # Context compartilhado entre agentes
├── SESSION_LOG.md              # Log de decisões e eventos
├── docs/                       # Documentação (Quick Specs, Tech-Specs, etc.)
│   ├── analytics_spec.md
│   ├── analytics_tech_spec.md
│   ├── analytics_impl.md
│   ├── stabilizer_notes.md
│   ├── rl_ablation.md
│   └── TEAM_OPERATING_AGREEMENT.md
├── contracts/                  # Contratos estruturados (JSON)
│   ├── events.schema.json
│   ├── events.jsonl
│   ├── analytics_plan.json
│   ├── analytics_interface.json
│   ├── acceptance_criteria.json
│   └── reward_profile.json
├── reports/                    # Relatórios e métricas
│   ├── analytics_qa.md
│   ├── metrics_snapshot.md
│   ├── coverage_map.md
│   ├── coverage_gaps.md
│   └── reward_changelog.md
└── bmad/                       # BMAD installation (não editar via LLM)
    └── _cfg/
        ├── teams/team-rl-core.yaml
        └── agents/
            ├── tech-lead.customize.yaml
            ├── analyst_pm.customize.yaml
            ├── architect.customize.yaml
            ├── dev.customize.yaml
            ├── qa_tea.customize.yaml
            ├── data_specialist.customize.yaml
            ├── reward_tuner.customize.yaml
            └── coverage_mapper.customize.yaml
```

---

## 🎯 Comandos Úteis

### Verificar eventos no bus

```bash
# Ver todos os eventos
cat contracts/events.jsonl

# Filtrar eventos por tipo
grep "SPEC_READY" contracts/events.jsonl
grep "DEV_DONE" contracts/events.jsonl
grep "QA_REPORT_READY" contracts/events.jsonl
```

### Validar schemas JSON

```bash
# Instalar ajv-cli (se necessário)
npm install -g ajv-cli

# Validar evento contra schema
echo '{"type":"SPEC_READY",...}' | ajv validate -s contracts/events.schema.json
```

### Gerar Quick Spec para múltiplos módulos

```bash
# Analytics
npx bmad-method@alpha workflow bmm/quick-spec-flow --module analytics

# Fees & Taxes
npx bmad-method@alpha workflow bmm/quick-spec-flow --module fees_taxes

# Integrations
npx bmad-method@alpha workflow bmm/quick-spec-flow --module integrations
```

---

## 🛡️ Guardrails e Violações

### O que fazer quando...

**Path Violation (escrita fora de ALLOWED WRITES)**
1. Tech-Lead aborta operação
2. Registra em `SESSION_LOG.md`
3. Notifica orquestrador externo (ClaudIA v3.1)

**Diff > 200 linhas**
1. Dev divide em múltiplos arquivos:
   - `analytics_impl_part1.md`
   - `analytics_impl_part2.md`
2. Adiciona referências cruzadas

**DoR Incompleto**
1. Tech-Lead bloqueia Dev
2. Solicita complemento ao Analyst/PM
3. Aguarda SPEC_READY atualizado

**Flake Rate > 30%**
1. QA/TEA escala para Architect + Dev
2. Revisar selectors e waits
3. Implementar heurísticas em `docs/stabilizer_notes.md`

---

## 📊 Métricas de Sucesso

Rastreadas pelo Data-Specialist em `reports/team_health.md`:

| Métrica | Target | Alerta se... |
|---------|--------|--------------|
| **Cycle Time** | < 4h | > 8h |
| **Pass Rate** | ≥ 80% | < 70% |
| **Reward A→D** | ≥ 0.7 | < 0.5 |
| **Coverage Growth** | +5% / ciclo | < 2% em 5 ciclos |
| **Rework Rate** | < 20% | > 30% |
| **Flake Rate** | < 10% | > 30% |

---

**Versão**: 1.0  
**Última Atualização**: 2025-11-10  
**Time**: team-rl-core (8 agentes)

