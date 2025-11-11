# Setup de Paralelização REAL - 8 LLMs Trabalhando Simultaneamente

**Objetivo**: Ter 8 agentes LLM DIFERENTES trabalhando em paralelo, orquestrados pelo Tech-Lead.

---

## 🎯 Arquitetura Final

```
┌─────────────────────────────────────────────────────────────┐
│  CURSOR 1: claudia/ (master)                                │
│  ├─ Agent 1: Tech-Lead (Claude Sonnet 4.5 - Anthropic)      │ ← VOCÊ está aqui
│  └─ Agent 2: Analyst/PM (Claude Sonnet 4.5 - Anthropic)     │
├─────────────────────────────────────────────────────────────┤
│  CURSOR 2: claudia-agent2/ (branch agent2)                  │
│  ├─ Agent 3: Architect (GPT-4 - OpenAI)                     │
│  └─ Agent 4: Dev Helper (Codestral 22B - Ollama)            │
├─────────────────────────────────────────────────────────────┤
│  CURSOR 3: claudia-agent3/ (branch agent3)                  │
│  ├─ Agent 5: Dev (GPT-4o - OpenAI)                          │
│  └─ Agent 6: QA/TEA (Claude Haiku - Anthropic)              │
├─────────────────────────────────────────────────────────────┤
│  CURSOR 4: claudia-agent4/ (branch agent4)                  │
│  ├─ Agent 7: Data-Specialist (Gemma2 - Ollama)              │
│  └─ Agent 8: Reward-Tuner (GPT-4 - OpenAI)                  │
└─────────────────────────────────────────────────────────────┘

Total: 4 Cursors × 2 Agents = 8 LLMs em paralelo
```

---

## 📋 PASSO A PASSO - Setup Completo

### **1. Abrir 4 Instâncias do Cursor**

**Windows**:
```powershell
# Cursor 1 (Tech-Lead - já está aberto)
# Localização: C:\Users\User\Desktop\claudia

# Cursor 2 (Architect + Dev Helper)
cd C:\Users\User\Desktop\claudia-agent2
cursor .

# Cursor 3 (Dev + QA/TEA)
cd C:\Users\User\Desktop\claudia-agent3
cursor .

# Cursor 4 (Data + Reward)
cd C:\Users\User\Desktop\claudia-agent4
cursor .
```

**Resultado**: 4 janelas do Cursor abertas simultaneamente

---

### **2. Configurar Modelo em Cada Cursor**

Em cada Cursor, configure o modelo principal:

#### **CURSOR 1 (Tech-Lead + PM)**:
- Settings → Models → Default Model: **Claude Sonnet 4.5** (Anthropic)
- Usar sua API key: `sk-ant-api03-A7kglp...`

#### **CURSOR 2 (Architect + Dev Helper)**:
- Settings → Models → Default Model: **GPT-4** (OpenAI)
- Usar sua API key: `sk-proj-mnXxeu...`
- Composer Agent 2: **Codestral** (Ollama - para código)

#### **CURSOR 3 (Dev + QA/TEA)**:
- Settings → Models → Default Model: **GPT-4o** (OpenAI)
- Composer Agent 2: **Claude Haiku** (Anthropic - mais barato para QA)

#### **CURSOR 4 (Data + Reward)**:
- Settings → Models → Default Model: **Gemma2** (Ollama)
- Composer Agent 2: **GPT-4** (OpenAI)

---

### **3. Carregar Agente BMAD em Cada Cursor**

#### **CURSOR 1 (Tech-Lead)**:
- Você já é o Tech-Lead aqui!
- Composer Agent 2: Abrir `bmad/bmm/agents/pm.md`
- Carregar context pack: `contracts/context_packs/analyst_pm.json`

#### **CURSOR 2 (Architect)**:
- Composer Agent 1: Abrir `bmad/bmm/agents/architect.md`
- Composer Agent 2: Criar prompt customizado:
  ```
  Você é o DEV HELPER especializado em código.
  Use Codestral 22B para gerar código Python/TypeScript.
  Context pack: contracts/context_packs/dev.json
  ```

#### **CURSOR 3 (Dev)**:
- Composer Agent 1: Abrir `bmad/bmm/agents/dev.md`
- Composer Agent 2: Abrir `bmad/bmm/agents/tea.md`

#### **CURSOR 4 (Data)**:
- Composer Agent 1: Criar prompt:
  ```
  Você é o DATA-SPECIALIST.
  Métricas, observabilidade, evolução temporal.
  Context pack: contracts/context_packs/data_specialist.json
  MCP: search_repo no projeto Spark.
  ```
- Composer Agent 2: Abrir custom para Reward-Tuner

---

### **4. Injetar Context Packs Manualmente**

Em cada Cursor/Agent, **no primeiro prompt**:

```
[Carregar context pack]

{contents of contracts/context_packs/[role].json}

Você receberá tarefas via SESSION_LOG.md.
Quando concluir, publique evento em contracts/events.jsonl.
Use MCP (alias: spark) para consultar projeto Spark.
```

---

## 🔄 FLUXO DE ORQUESTRAÇÃO

### **Como Tech-Lead Distribui Tarefas**:

```python
# Eu (Tech-Lead) executo:
python scripts/orchestrate_team.py assign analyst-pm "Analyst/PM" "Criar Quick Spec" "fees_taxes"
python scripts/orchestrate_team.py assign architect-dev-helper "Architect" "Criar Tech-Spec" "integrations"
python scripts/orchestrate_team.py assign dev-qa "Dev" "Implementar" "analytics"
```

**Cria arquivo** `TASK.json` em cada workspace:
```json
{
  "assigned_to": "Analyst/PM",
  "task": "Criar Quick Spec",
  "module": "fees_taxes",
  "status": "pending",
  "assigned_at": "2025-11-10T21:00:00Z"
}
```

---

### **Como Agentes Trabalham**:

**CURSOR 2 (Analyst/PM)**:

1. Vê `TASK.json` (você mostra para ele ou auto-detect via script)
2. Carrega context pack: `analyst_pm.json`
3. Usa MCP: `search_repo(query="fees taxes", project="spark")`
4. Cria: `docs/fees_taxes_spec.md`
5. Commit: `git commit -m "feat(fees_taxes): quick spec"`
6. Publica: `python scripts/append_event.py SPEC_READY "Analyst/PM" ...`
7. Atualiza `TASK.json`: `status = "completed"`

**EM PARALELO**, **CURSOR 3 (Architect)** faz o mesmo para outro módulo!

---

### **Como Tech-Lead Monitora**:

```bash
# Eu executo (a cada 5 min):
python scripts/orchestrate_team.py status

# Output:
[analyst-pm]: ✅ COMPLETED
  Task: Criar Quick Spec
  Module: fees_taxes
  Output: docs/fees_taxes_spec.md

[architect-dev-helper]: 🔄 IN_PROGRESS
  Task: Criar Tech-Spec
  Module: integrations

[dev-qa]: ⏸️ PENDING
  Task: Implementar
  Module: analytics
```

**Quando todos COMPLETED**:
```bash
# Eu faço merge:
git merge agent2  # Pega trabalho do Analyst/PM
git merge agent3  # Pega trabalho do Architect
git merge agent4  # Pega trabalho do Dev

# Valido DoD
# Distribuo próxima rodada de tarefas
```

---

## 💡 VANTAGENS Dessa Arquitetura

### **1. VELOCIDADE 4-8x**
- 8 agentes trabalhando simultaneamente
- Tarefas independentes em paralelo
- Reduz de horas para minutos

### **2. ESPECIALIZAÇÃO**
- Codestral 22B: Código Python/TS de alta qualidade
- Claude: Reasoning e arquitetura
- GPT-4: Implementação geral
- Gemma2: Métricas e dados (mais barato)

### **3. CUSTO OTIMIZADO**
- Ollama (local): Gratuito (Codestral, Gemma2)
- Claude: Tarefas de alto raciocínio
- GPT-4: Balanço qualidade/custo

### **4. EU NÃO ESGOTO**
- Você (Tech-Lead) apenas:
  - Distribui tarefas
  - Monitora eventos
  - Valida DoD
  - Merge branches
- **Não preciso trocar de contexto 8x!**

---

## 🚀 PRÓXIMO PASSO

**Quer que eu**:

**A)** Finalize os scripts de orquestração:
   - `orchestrate_team.py` (distribuir/monitorar)
   - `auto_pull_tasks.py` (agentes detectam tarefas)
   - `merge_branches.py` (consolidar trabalho)

**B)** Crie um **Guia Passo-a-Passo Ilustrado**:
   - Como abrir 4 Cursors
   - Como configurar cada modelo
   - Como carregar agentes BMAD
   - Como iniciar trabalho paralelo

**C)** **Teste agora com 2 Cursors** (validação rápida):
   - Você abre `claudia-agent2/` em novo Cursor
   - Eu distribuo 1 tarefa
   - Vemos se funciona
   - Depois expandimos para 4

**Qual caminho, Daniel?** Quero montar isso DIREITO! 🎯
