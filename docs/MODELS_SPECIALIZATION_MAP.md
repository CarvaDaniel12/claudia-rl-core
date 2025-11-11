# Mapeamento de Modelos por Especialização - Time RL Core

**Objetivo**: Escolher o modelo IDEAL para cada papel, baseado em performance conhecida

---

## 🏆 MODELOS POR CATEGORIA (Conhecimento Geral)

### **CODING** (geração de código)

**Melhores**:
1. **Codestral 22B** (Mistral - Ollama) - GRÁTIS, especializado
2. **DeepSeek Coder V2** (Ollama) - GRÁTIS, muito bom
3. **Qwen2.5-Coder 32B** (Ollama) - GRÁTIS, excelente
4. **GPT-4 Turbo** (OpenAI) - PAGO, versátil
5. **Claude Sonnet 4.5** (Anthropic) - PAGO, bom mas caro

**Recomendação para Dev**: **Codestral 22B** (local, grátis, especializado)

---

### **REASONING** (arquitetura, decisões, análise)

**Melhores**:
1. **Claude Sonnet 4.5** (Anthropic) - MELHOR reasoning
2. **GPT-4o** (OpenAI) - Balanceado (reasoning + velocidade)
3. **o1-preview** (OpenAI) - Reasoning extremo (MUITO caro)
4. **Gemini Pro 1.5** (Google) - Bom, janela gigante

**Recomendação para Architect/PM**: **Claude Sonnet 4.5**

---

### **TESTING** (QA, assertions, validação)

**Melhores**:
1. **Claude Haiku** (Anthropic) - Rápido, barato, suficiente
2. **GPT-4o mini** (OpenAI) - Muito barato, rápido
3. **Gemma2 9B** (Ollama) - GRÁTIS, básico mas funciona

**Recomendação para QA/TEA**: **Claude Haiku** (barato, rápido)

---

### **DATA ANALYSIS** (métricas, agregações)

**Melhores**:
1. **GPT-4 Data Analyst** (OpenAI) - Especializado
2. **Claude Sonnet 4.5** - Bom para análise de logs
3. **Gemma2 27B** (Ollama) - GRÁTIS, ok para agregações simples

**Recomendação para Data-Specialist**: **Gemma2 27B** (local, grátis, suficiente)

---

## 🎯 TIME RL CORE - MAPEAMENTO FINAL

| Papel | Modelo Principal | Fallback | Custo/Ciclo | Justificativa |
|-------|------------------|----------|-------------|---------------|
| **Tech-Lead** | Claude Sonnet 4.5 | GPT-4o | $1.50 | Reasoning + orquestração |
| **Analyst/PM** | Claude Sonnet 4.5 | GPT-4 | $1.50 | Specs claros + reasoning |
| **Architect** | GPT-4 Turbo | Claude Sonnet | $1.00 | Design técnico balanceado |
| **Dev** | **Codestral 22B (Ollama)** | GPT-4 Turbo | **$0.00** | Código especializado, LOCAL |
| **Dev Helper** | **DeepSeek Coder (Ollama)** | Qwen Coder | **$0.00** | Code generation, LOCAL |
| **QA/TEA** | Claude Haiku | GPT-4o mini | $0.30 | Rápido, barato, testes |
| **Data-Specialist** | **Gemma2 27B (Ollama)** | GPT-4 | **$0.00** | Métricas simples, LOCAL |
| **Reward-Tuner** | Claude Sonnet 4.5 | GPT-4 | $1.00 | Math + reasoning RL |
| **Coverage-Mapper** | GPT-4o | Gemma2 | $0.80 | Mapas + análise rápida |

**Total Estimado/Ciclo**: ~$6.10 (3 agentes GRÁTIS via Ollama)

**Com Ollama**: Economia de ~40-50% vs tudo pago

---

## 🔧 CONFIGURAÇÃO OLLAMA

### Modelos a Baixar

```bash
# Código (Dev + Dev Helper)
ollama pull codestral:22b
ollama pull deepseek-coder-v2:16b

# Dados (Data-Specialist)
ollama pull gemma2:27b

# Embeddings (MCP - já baixado)
ollama pull nomic-embed-text

# Opcional (testes)
ollama pull qwen2.5-coder:32b
```

### Variáveis de Ambiente

```bash
# Já configuradas em mcp.json:
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_NUM_PARALLEL=1
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Adicionar (performance):
OLLAMA_MAX_LOADED_MODELS=3  # Dev, Dev Helper, Data
OLLAMA_KEEP_ALIVE=10m       # Manter modelos carregados
```

---

## 🚀 ESTRATÉGIAS DE ORQUESTRAÇÃO

### **Estratégia A: Cursor Nativo** (SE descobrirmos como)

```
[1 Cursor - Parallel Agents Ativado]

Agent 1: Tech-Lead (Claude Sonnet)     │
Agent 2: Analyst/PM (Claude Sonnet)    │
Agent 3: Architect (GPT-4)             │ SIMULTÂNEO
Agent 4: Dev (Codestral - Ollama)      │
Agent 5: QA/TEA (Claude Haiku)         │
Agent 6: Data (Gemma2 - Ollama)        │
Agent 7: Reward (Claude Sonnet)        │
Agent 8: Coverage (GPT-4o)             │
```

**Orquestração**: Via Cursor nativo (painel de agentes?)

---

### **Estratégia B: Múltiplas Abas** (Provável Solução)

```
[1 Cursor - 8 Abas de Chat]

Aba 1: Tech-Lead (Claude Sonnet) - Orquestra
Aba 2: Analyst/PM (Claude Sonnet) - Task A
Aba 3: Architect (GPT-4) - Task B
Aba 4: Dev (Codestral) - Task C
Aba 5: Dev Helper (DeepSeek) - Auxilia Aba 4
Aba 6: QA/TEA (Haiku) - Task D
Aba 7: Data (Gemma2) - Task E
Aba 8: Reward (GPT-4o) - Task F
```

**Orquestração**: Tech-Lead (Aba 1) distribui via SESSION_LOG.md

**Como funciona**:
1. Tech-Lead escreve tarefa em SESSION_LOG.md
2. Você copia tarefa + context pack para cada aba
3. Cada aba trabalha independentemente
4. Resultados voltam para SESSION_LOG.md via commits

---

### **Estratégia C: Worktrees + Abas** (Máxima Potência)

```
[Cursor 1: claudia/]
├─ Aba 1: Tech-Lead (Claude Sonnet)
└─ Aba 2: Analyst/PM (Claude Sonnet)

[Cursor 2: agent2/]
├─ Aba 1: Architect (GPT-4)
└─ Aba 2: Dev Helper (Codestral - Ollama)

[Cursor 3: agent3/]
├─ Aba 1: Dev (DeepSeek - Ollama)
└─ Aba 2: QA/TEA (Claude Haiku)

[Cursor 4: agent4/]
├─ Aba 1: Data (Gemma2 - Ollama)
└─ Aba 2: Reward (GPT-4o)
```

**Total**: 4 Cursors × 2 Abas = **8 agentes independentes**

**Orquestração**: Git + Event Bus + SESSION_LOG.md

---

## ⏱️ ESTIMATIVA DE VELOCIDADE

### **1 Agente (Atual - EU sozinho)**:
- Criar 3 specs: ~90 min
- Implementar 3 módulos: ~3-4 horas

### **8 Agentes Paralelos**:
- Criar 3 specs: ~15-20 min (6x mais rápido)
- Implementar 3 módulos: ~45 min (5x mais rápido)

**Ganho**: **4-6x mais rápido** com time completo! 🚀

---

**AGUARDANDO SEUS TESTES, DANIEL!** 🔍

Me mande screenshots ou textos do que encontrar! Vamos resolver isso juntos!

