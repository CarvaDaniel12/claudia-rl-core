# Team Operating Agreement - RL Core Team

## Objetivo

Simular uma equipe real multidisciplinar com regras claras, handoffs determinísticos e comunicação baseada em eventos para desenvolvimento de sistemas RL Atômico.

---

## Guardrails Globais

### ALLOWED WRITES
- `AGENT_CONTEXT.json`
- `SESSION_LOG.md`
- `contracts/*.json`
- `reports/*.md`
- `docs/*.md`

**⚠️ REGRA CRÍTICA**: Diffs ≤ 200 linhas por arquivo

**Violação → Abortar operação + Registrar em SESSION_LOG.md + Notificar Tech-Lead**

---

## Sistema de Eventos

### Event Bus: `contracts/events.jsonl`

Formato JSON Lines (um evento por linha, aderente a `contracts/events.schema.json`)

### Eventos Core

#### 1. `SPEC_READY`
```json
{"type":"SPEC_READY","timestamp":"2025-11-10T10:00:00Z","actor":"Analyst/PM","payload":{"module":"analytics","spec_path":"docs/analytics_spec.md"}}
```
**Dispara**: Architect + Dev  
**Quando**: Quick Spec aprovado pelo Analyst/PM

#### 2. `DEV_DONE`
```json
{"type":"DEV_DONE","timestamp":"2025-11-10T12:00:00Z","actor":"Dev","payload":{"module":"analytics","artifacts":["contracts/analytics_plan.json","docs/analytics_impl.md"]}}
```
**Dispara**: QA/TEA  
**Quando**: Implementação concluída nos paths permitidos

#### 3. `QA_REPORT_READY`
```json
{"type":"QA_REPORT_READY","timestamp":"2025-11-10T14:00:00Z","actor":"QA/TEA","payload":{"module":"analytics","pass_rate":0.85,"blockers":["selector-timeout-login"],"report":"reports/analytics_qa.md"}}
```
**Dispara**: Tech-Lead + Data-Specialist  
**Quando**: Avaliação completa com evidências

#### 4. `METRICS_UPDATED`
```json
{"type":"METRICS_UPDATED","timestamp":"2025-11-10T15:00:00Z","actor":"Data-Specialist","payload":{"run_id":"run_042","reward":0.72,"pass_rate":0.85,"duration_s":120}}
```
**Dispara**: Tech-Lead + Reward-Tuner  
**Quando**: Métricas consolidadas em rl_atomic/evolution.json

---

## Definition of Ready (DoR)

Checklist antes de Dev iniciar implementação:

- [ ] Quick Spec aprovado e publicado
- [ ] Critérios de aceitação claros e testáveis
- [ ] Pontos de integração mapeados pelo Architect
- [ ] Dados de teste/mocks definidos
- [ ] SPEC_READY publicado no event bus

**Responsável**: Tech-Lead valida; Analyst/PM + Architect fornecem

---

## Definition of Done (DoD)

Checklist antes de fechar história/módulo:

- [ ] Implementação ou documento produzido em path permitido
- [ ] Diff ≤ 200 linhas por arquivo
- [ ] QA/TEA executou avaliação e gerou relatório (`reports/*.md`)
- [ ] Métricas do run atualizadas (`rl_atomic/evolution.json`)
- [ ] Schemas JSON validados
- [ ] Evidências reprodutíveis anexadas
- [ ] QA_REPORT_READY publicado

**Responsável**: Tech-Lead valida; QA/TEA + Data-Specialist fornecem

---

## RACI Matrix

| Atividade | Responsible | Accountable | Consulted | Informed |
|-----------|-------------|-------------|-----------|----------|
| **Planejamento (Spec/Plan)** | Analyst/PM | Tech-Lead | Architect | Dev, QA, Data |
| **Arquitetura (Tech-Spec)** | Architect | Tech-Lead | Analyst/PM, Dev | QA, Data |
| **Implementação (Docs/Contracts)** | Dev | Tech-Lead | Architect, Analyst/PM | QA, Data |
| **Testes (Eval/Asserts)** | QA/TEA | Tech-Lead | Dev | Data |
| **Métricas/RL (Rewards/Evolution)** | Data-Specialist, Reward-Tuner | Tech-Lead | QA, Dev | Analyst/PM, Architect |
| **Revisão/Gate (Qualidade)** | Tech-Lead | Tech-Lead | QA, Reviewer | Todos |

---

## Fluxo de Handoff Completo

```
1. Analyst/PM → SPEC_READY → [Architect + Dev]
2. Architect → Tech-Spec (docs/) → Dev consulta
3. Dev → DEV_DONE → [QA/TEA]
4. QA/TEA → QA_REPORT_READY → [Tech-Lead + Data-Specialist]
5. Data-Specialist → METRICS_UPDATED → [Tech-Lead + Reward-Tuner]
6. Tech-Lead → Decide: aprovar | iterar | escalar
```

---

## Papéis Detalhados

### 1. Tech-Lead
- **Orquestra**: Fluxo completo, aplica guardrails
- **Valida**: DoR (antes Dev) + DoD (antes fechar)
- **Decide**: Handoffs, prioridades, escalações
- **Entregas**: `SESSION_LOG.md`, `docs/tech_lead_notes.md`

### 2. Analyst/PM
- **Produz**: PRD, Quick Spec, story map
- **Publica**: `SPEC_READY` quando módulo aprovado
- **Garante**: Critérios testáveis ligados ao QA/TEA
- **Entregas**: `docs/*_spec.md`, `docs/backlog.md`

### 3. Architect
- **Converte**: Spec → Tech-Spec (interfaces/fluxos/erros)
- **Coordena**: Com Dev e QA para testabilidade
- **Projeta**: Waits semânticos, selectors estáveis
- **Entregas**: `docs/*_tech_spec.md`, `contracts/*_interface.json`

### 4. Dev
- **Implementa**: Artefatos em paths permitidos
- **Publica**: `DEV_DONE` com lista de artifacts
- **Respeita**: 200 linhas/arquivo, schemas JSON
- **Entregas**: `contracts/*.json`, `docs/*_impl.md`

### 5. QA/TEA (Test Architect)
- **Executa**: 1 run com asserts mínimos + waits semânticos
- **Gera**: Relatório com pass_rate e evidências
- **Publica**: `QA_REPORT_READY` com blockers
- **Propõe**: Heurísticas anti-flake em `docs/stabilizer_notes.md`
- **Entregas**: `reports/*_qa.md`, `docs/test_strategy.md`

### 6. Data-Specialist (Observer)
- **Monitora**: `assertions_pass_rate`, `selector_success_rate`, `reward`, `duration`
- **Atualiza**: `rl_atomic/evolution.json`
- **Publica**: `METRICS_UPDATED` após cada run
- **Analisa**: Tendências, thresholds, alertas
- **Entregas**: `reports/metrics_snapshot.md`, `docs/observability.md`

### 7. Reward-Tuner
- **Calibra**: Reward A→D (α,β,γ,δ,ε,K,p), caps, penalidades
- **Experimenta**: Ablação (masking ON/OFF, curiosity vs count, HRL)
- **Reage**: `METRICS_UPDATED` → propõe ajustes baseados em evidência
- **Entregas**: `contracts/reward_profile.json`, `docs/rl_ablation.md`

### 8. Coverage-Mapper
- **Consolida**: `playwright_knowledge.json` + runs recentes
- **Mapeia**: % cobertura de rotas/estados/affordances
- **Prioriza**: Top 10 lacunas + 5 rotas alvo para Explorer
- **Entregas**: `reports/coverage_map.md`, `docs/exploration_targets.md`

---

## Regras de Exceção

1. **Path Violation**: Tech-Lead aborta, registra em `SESSION_LOG.md`, notifica orquestrador externo (ClaudIA)
2. **Diff > 200 linhas**: Dev/QA dividem em múltiplos arquivos (ex: `part1.md`, `part2.md`)
3. **DoR Incompleto**: Tech-Lead bloqueia Dev, solicita complemento ao Analyst/PM
4. **DoD Incompleto**: Tech-Lead não fecha história, retorna para papel responsável
5. **Flake Rate > 30%**: QA/TEA escala para Architect + Dev revisarem selectors/waits

---

## Métricas de Saúde do Time

Rastreadas pelo Data-Specialist em `reports/team_health.md`:

- **Cycle Time**: SPEC_READY → QA_REPORT_READY
- **Rework Rate**: % de stories retornadas após DoD
- **Pass Rate Trend**: Evolução do pass_rate por módulo
- **Reward Stability**: Variância do reward A→D
- **Coverage Growth**: Incremento semanal de rotas mapeadas

---

**Versão**: 1.0  
**Última Atualização**: 2025-11-10  
**Time**: team-rl-core

