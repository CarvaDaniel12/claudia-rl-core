# Quick Spec: Analytics Module

**Módulo**: analytics  
**Versão**: 1.0  
**Data**: 2025-11-10  
**Autor**: Analyst/PM

---

## Visão Geral

O módulo **Analytics** é responsável por rastrear, consolidar e reportar métricas de exploração RL Atômica, incluindo:
- Assertions pass rate
- Selector success rate  
- Reward A→D
- Coverage (rotas/estados/affordances)
- Duration e performance

---

## Objetivos de Negócio

1. **Verdade Única**: Cada run tem métricas consolidadas e imutáveis
2. **Evolução Temporal**: Rastrear tendências ao longo de múltiplos runs
3. **Alertas Proativos**: Detectar regressões (pass_rate < 70%, reward < 0.5)
4. **Suporte a Decisão**: Tech-Lead e Reward-Tuner usam métricas para ajustes

---

## Casos de Uso

### UC1: Registrar Métricas de Run
**Ator**: Data-Specialist (Observer)  
**Pré-condição**: Run concluído com logs disponíveis  
**Fluxo**:
1. Coletar métricas do run (assertions, selectors, reward, duration)
2. Validar completude (todos os campos obrigatórios presentes)
3. Salvar em `rl_atomic/evolution.json` (append)
4. Publicar evento `METRICS_UPDATED`

**Pós-condição**: Métricas disponíveis para análise

---

### UC2: Gerar Snapshot de Métricas
**Ator**: Data-Specialist  
**Pré-condição**: Pelo menos 1 run registrado  
**Fluxo**:
1. Ler último run de `rl_atomic/evolution.json`
2. Calcular agregações (média/percentis últimos 5 runs)
3. Gerar `reports/metrics_snapshot.md`
4. Incluir gráfico de tendência (tabela markdown)

**Pós-condição**: Snapshot legível para humanos disponível

---

### UC3: Detectar Alertas
**Ator**: Data-Specialist  
**Pré-condição**: Métricas de run registradas  
**Fluxo**:
1. Comparar pass_rate com threshold (< 70%)
2. Comparar reward com threshold (< 0.5)
3. Verificar estagnação de coverage (< 2% em 5 runs)
4. Se alerta detectado, adicionar em `reports/alerts.md`
5. Publicar evento `BLOCKER_RAISED` (se crítico)

**Pós-condição**: Tech-Lead notificado de regressões

---

## Critérios de Aceitação

### ✅ CA1: Métricas Completas
- [ ] Cada run inclui: `run_id`, `timestamp`, `assertions_pass_rate`, `selector_success_rate`, `reward`, `duration_s`, `coverage`
- [ ] Schema JSON validado contra `contracts/analytics_schema.json`
- [ ] Imutabilidade: runs não são editados após serem salvos

### ✅ CA2: Evolução Temporal
- [ ] `rl_atomic/evolution.json` contém array de runs (ordem cronológica)
- [ ] Suporte a query: "últimos N runs"
- [ ] Cálculo de tendências (média móvel últimos 5 runs)

### ✅ CA3: Alertas Configuráveis
- [ ] Thresholds definidos em `contracts/alert_config.json`
- [ ] Alertas incluem: tipo, severity, timestamp, mensagem, run_id
- [ ] Histórico de alertas em `reports/alerts.md`

### ✅ CA4: Snapshot Legível
- [ ] `reports/metrics_snapshot.md` atualizado após cada run
- [ ] Inclui: último run, tendências (5 runs), alertas ativos
- [ ] Formato markdown com tabelas

---

## Pontos de Integração

### Entrada (Dados de Run)
- **Fonte**: QA/TEA (após executar testes)
- **Formato**: JSON com campos: `run_id`, `timestamp`, `assertions`, `selectors`, `reward`, `duration_s`
- **Contrato**: `contracts/run_data_schema.json`

### Saída (Métricas Consolidadas)
- **Destino**: Tech-Lead (decisões), Reward-Tuner (ajustes)
- **Formato**: JSON (`rl_atomic/evolution.json`) + Markdown (`reports/metrics_snapshot.md`)
- **Evento**: `METRICS_UPDATED` via event bus

### Integração com Coverage-Mapper
- **Dado compartilhado**: `coverage` (% de rotas/estados visitados)
- **Sincronização**: Coverage-Mapper lê de `rl_atomic/evolution.json`

---

## Dados de Teste

### Cenário 1: Run com Sucesso
```json
{
  "run_id": "run_001",
  "timestamp": "2025-11-10T18:00:00Z",
  "assertions_pass_rate": 0.92,
  "selector_success_rate": 0.95,
  "reward": 0.78,
  "duration_s": 85,
  "coverage": 0.65
}
```

### Cenário 2: Run com Alerta (Pass Rate Baixo)
```json
{
  "run_id": "run_042",
  "timestamp": "2025-11-10T19:00:00Z",
  "assertions_pass_rate": 0.62,
  "selector_success_rate": 0.88,
  "reward": 0.45,
  "duration_s": 120,
  "coverage": 0.58
}
```
**Alerta esperado**: `pass_rate < 70%` e `reward < 0.5`

---

## Restrições Técnicas

1. **ALLOWED WRITES**: 
   - `rl_atomic/evolution.json` (via scripts externos)
   - `reports/metrics_snapshot.md`
   - `reports/alerts.md`
   - `contracts/analytics_schema.json`

2. **Diff Limit**: ≤ 200 linhas por arquivo

3. **Performance**: 
   - Agregação de métricas deve completar em < 5s (até 1000 runs)
   - `evolution.json` deve ser append-only (não reescrever)

4. **Atomicidade**: 
   - Usar lockfile para evitar race conditions em writes

---

## Dependências

- **Python**: Módulos `json`, `datetime`, `pathlib`, `statistics`
- **Schema Validation**: jsonschema (já instalado)
- **Event Bus**: `scripts/append_event.py` (já criado)

---

## Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| `evolution.json` cresce muito (> 10MB) | Médio | Alto | Rotação: mover runs antigos para `archive/` mensalmente |
| Race condition em writes | Baixo | Alto | Lockfile (já implementado em append_event.py) |
| Schema muda e quebra runs antigos | Baixo | Médio | Versionamento de schema + migração |

---

## Entregáveis

1. `contracts/analytics_schema.json` - Schema de métricas
2. `contracts/alert_config.json` - Configuração de thresholds
3. `scripts/aggregate_metrics.py` - Consolidação de métricas
4. `reports/metrics_snapshot.md` - Snapshot legível
5. `reports/alerts.md` - Histórico de alertas

---

**Aprovado por**: Tech-Lead  
**Próximo passo**: Tech-Spec (Architect)

