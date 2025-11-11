# Pesquisa: Orquestração Paralela de Agentes - Time RL Core

**Data**: 2025-11-10  
**Tech-Lead**: Daniel + Claude  
**Objetivo**: Montar time de 8+ LLMs trabalhando em paralelo

---

## 🎯 Requisitos

### O Que Temos

✅ **Infraestrutura**:
- Cursor Ultra Plan (você - Daniel)
- 4 Worktrees (claudia, agent2, agent3, agent4)
- MCP indexado (projeto Spark) com Ollama embeddings
- Context packs (8 papéis + global)
- Event bus (contracts/events.jsonl)

✅ **API Keys**:
- Anthropic (Claude Sonnet 4.5, Haiku)
- OpenAI (GPT-4, GPT-4o, GPT-4 Turbo)
- Ollama local (Codestral 22B, Gemma2, etc.)

✅ **Agentes BMAD**:
- 8 papéis definidos com prompts customizados
- Heartbeat config (anti-amnésia)
- Guardrails e allowed writes

---

## 🔍 INVESTIGAÇÃO: Cursor Composer

### O Que Vimos na UI

Na sua screenshot:
- Opção "Composer 1" (desabilitada)
- "Auto" mode (toggle off)
- "MAX Mode" (toggle off)
- Múltiplos modelos disponíveis:
  - Sonnet 4.5
  - GPT-5 Codex High
  - GPT-5
  - Haiku 4.5
  - Grok Code
  - Sonnet 4

### Questões a Investigar

1. **Como ativar Composer múltiplos agentes no Cursor Pro/Ultra?**
   - Precisa habilitar algo nas settings?
   - É feature beta que precisa opt-in?
   - Tem documentação oficial?

2. **Diferença entre Auto, Agent, MAX Mode?**
   - Auto: Cursor escolhe modelo automaticamente?
   - Agent: Modo agente individual?
   - MAX: Modo máxima performance?

3. **Como configurar múltiplos Composers?**
   - Composer 1, Composer 2, etc.
   - Cada um com modelo diferente?
   - Trabalham em paralelo ou sequencial?

---

## 🤖 MODELOS: Quem é Melhor para Quê

### Pesquisa de Benchmarks (Conhecimento Geral)

#### **CODING** (HumanEval, MBPP)

**Top Tier**:
1. **Codestral 22B** (Mistral) - 81.0% HumanEval
2. **GPT-4 Turbo** (OpenAI) - 85.4% HumanEval
3. **Claude Sonnet 4.5** (Anthropic) - ~80% HumanEval

**Mid Tier**:
4. **DeepSeek Coder 33B** - 79% HumanEval (local)
5. **Qwen2.5 Coder 32B** - 78% (local)

**Budget**:
6. **Gemma2 9B** - ~60% (local, rápido)

#### **REASONING** (GPQA, MATH, Logic)

**Top Tier**:
1. **Claude Sonnet 4.5** - Melhor para reasoning profundo
2. **GPT-4o** - Balanceado (reasoning + velocidade)
3. **o1-preview** (OpenAI) - Reasoning extremo (caro)

**Mid Tier**:
4. **Gemini Pro 1.5** - Bom reasoning, janela gigante
5. **Gemma2 27B** - Reasoning local (mais lento)

#### **ANÁLISE DE DADOS**

1. **GPT-4 Data Analysis** - Excel, pandas, visualização
2. **Claude Sonnet 4.5** - Análise de logs, métricas
3. **Gemma2** - Local, bom para agregações simples

---

## 🎭 MAPEAMENTO: Papel → Modelo Ideal

### **Estratégia por Orçamento de Tokens**

| Papel | Tarefa Principal | Modelo Ideal | Fallback | Justificativa |
|-------|------------------|--------------|----------|---------------|
| **Tech-Lead** | Orquestração, decisões | Claude Sonnet 4.5 | GPT-4o | Reasoning profundo + context longo |
| **Analyst/PM** | Specs, requisitos | Claude Sonnet 4.5 | GPT-4 | Reasoning + escrita clara |
| **Architect** | Design, arquitetura | GPT-4 Turbo | Claude Sonnet | Balanço técnico + criativo |
| **Dev** | Implementação código | **Codestral 22B (Ollama)** | GPT-4 Turbo | Especializado em código, GRÁTIS |
| **Dev Helper** | Code generation | **DeepSeek Coder 33B** | Codestral | Complementa Dev, local |
| **QA/TEA** | Testes, assertions | Claude Haiku | GPT-4o mini | Rápido, barato, bom para testes |
| **Data-Specialist** | Métricas, análise | **Gemma2 27B (Ollama)** | GPT-4 | Dados simples, GRÁTIS |
| **Reward-Tuner** | Calibração RL | Claude Sonnet 4.5 | GPT-4 | Reasoning matemático |
| **Coverage-Mapper** | Análise cobertura | GPT-4o | Gemma2 | Rápido, bom para mapas |

### **Custo Estimado por Ciclo**

**Com Ollama (3 agentes locais)**:
- Codestral (Dev): GRÁTIS
- DeepSeek (Dev Helper): GRÁTIS
- Gemma2 (Data): GRÁTIS

**APIs (5 agentes)**:
- Claude Sonnet 4.5 × 3 (Tech, PM, Reward): ~$3-5/ciclo
- GPT-4 × 2 (Architect, Coverage): ~$2-3/ciclo
- Claude Haiku (QA): ~$0.50/ciclo

**Total/ciclo**: ~$5-9 (3 agentes grátis = economia de 40%)

---

## 🛠️ ARQUITETURA PROPOSTA

### **Opção 1: Cursor Composer Nativo** (SE conseguirmos ativar)

```
[1 Cursor - Múltiplos Composers]

Composer 1 (Tech-Lead): Claude Sonnet 4.5
Composer 2 (Analyst/PM): Claude Sonnet 4.5
Composer 3 (Architect): GPT-4
Composer 4 (Dev): Codestral 22B (Ollama)
Composer 5 (Dev Helper): DeepSeek Coder (Ollama)
Composer 6 (QA/TEA): Claude Haiku
Composer 7 (Data): Gemma2 (Ollama)
Composer 8 (Reward): GPT-4

TODOS na mesma janela, trabalhando em paralelo!
```

**Vantagens**:
- 1 Cursor (simples)
- Paralelização nativa
- Compartilhamento de contexto fácil

**Desafios**:
- Precisa descobrir como ativar
- Pode ter limite de Composers simultâneos

---

### **Opção 2: Worktrees + Composer Duplo** (Híbrido)

```
[Cursor 1: claudia/]
├─ Composer 1: Tech-Lead (Claude Sonnet)
└─ Composer 2: Analyst/PM (Claude Sonnet)

[Cursor 2: agent2/]
├─ Composer 1: Architect (GPT-4)
└─ Composer 2: Dev Helper (Codestral - Ollama)

[Cursor 3: agent3/]
├─ Composer 1: Dev (GPT-4o)
└─ Composer 2: QA/TEA (Claude Haiku)

[Cursor 4: agent4/]
├─ Composer 1: Data-Specialist (Gemma2 - Ollama)
└─ Composer 2: Reward-Tuner (GPT-4)
```

**Vantagens**:
- 2 agentes por Cursor (gerenciável)
- Branches separadas (isolamento Git)
- Usa worktrees que já criamos

**Desafios**:
- Precisa gerenciar 4 janelas
- Coordenação via Git + eventos

---

## 🔧 PRÓXIMAS AÇÕES (Tech-Lead)

### **INVESTIGAÇÃO - Cursor Composer**

**Perguntas para resolver**:

1. **Como ativar múltiplos Composers no Cursor?**
   - Checar: Settings → Agents → Enable Multiple Agents?
   - Checar: Experimental Features?
   - Checar: Cursor Docs/Blog sobre Composer

2. **Limite de agentes simultâneos**:
   - Ultra Plan: quantos Composers?
   - Pro Plan: quantos Composers?

3. **Como configurar modelo por Composer**:
   - Composer 1 = Claude
   - Composer 2 = GPT-4
   - Composer 3 = Ollama
   - etc.

---

### **TESTE RÁPIDO - Validar Conceito**

**Passo 1**: Tentar ativar Composer múltiplos agentes
- Settings → buscar "composer" ou "multiple agents"
- Experimental features?
- Beta opt-in?

**Passo 2**: Se não funcionar, testar Opção 2 (Worktrees + Duplo)
- Abrir `claudia-agent2/` em novo Cursor
- Configurar 2 Composers (Architect + Dev Helper)
- Distribuir 1 tarefa
- Ver se trabalham em paralelo

---

## 🎯 ESTRATÉGIA FINAL (A Definir)

**SE conseguirmos ativar Composers múltiplos**:
→ Opção 1 (1 Cursor, 8 Composers) - IDEAL

**SE não conseguirmos**:
→ Opção 2 (4 Cursors, 2 Composers cada) - VIÁVEL

**SE Cursor não permitir múltiplos na mesma instância**:
→ Worktrees com 1 agente cada (mais manual, mas funciona)

---

## 📚 REFERÊNCIAS

- [BMAD Method GitHub](https://github.com/bmad-code-org/BMAD-METHOD)
- [BMAD Party Mode Docs](./WORKFLOW_GUIDE.md)
- Cursor Composer (precisa documentação oficial)

---

## 🚀 PRÓXIMO PASSO IMEDIATO

**Daniel, vamos fazer juntos**:

1. **Você**: Abrir Settings do Cursor → Buscar "composer" ou "agents" ou "experimental"
2. **Eu**: Enquanto isso, termino scripts de orquestração
3. **Juntos**: Definimos estratégia final (Opção 1 ou 2)

**Pode checar as Settings agora?** 🔍

Me diga o que encontrou sobre:
- Múltiplos agentes/Composers
- Experimental features
- Agent settings

---

**Estou pronto para adaptar a estratégia ao que descobrirmos!** 🎯

