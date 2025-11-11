# Investigação: Cursor Ultra - Parallel Agents

**Data**: 2025-11-10  
**Plano**: Ultra ($200/mês)  
**Descrição do Plano**: "Run parallel agents, get maximum value with 20x usage limits"

**Problema**: Feature de "parallel agents" não está visível/ativável

---

## 🔍 CHECKLIST DE INVESTIGAÇÃO

### 1. Settings → Agents

**Caminho**: Cursor → Settings (Ctrl+,) → Buscar "agent"

**O que procurar**:
- [ ] "Enable Parallel Agents" (checkbox)
- [ ] "Max Concurrent Agents" (número)
- [ ] "Multi-Agent Mode" (toggle)
- [ ] "Beta Features" → "Parallel Processing"

**Status**: INVESTIGAR AGORA

---

### 2. Settings → Beta / Experimental

**Caminho**: Settings → Buscar "beta" ou "experimental"

**O que procurar**:
- [ ] "Enable Experimental Features"
- [ ] "Parallel Agent Execution"
- [ ] "Multi-Model Inference"

**Status**: INVESTIGAR AGORA

---

### 3. Settings → Models

**Caminho**: Settings → Models

**O que procurar**:
- [ ] "Composer Settings"
- [ ] "Agent Configuration"
- [ ] "Parallel Execution"
- [ ] Opção de múltiplos modelos simultâneos

**Status**: INVESTIGAR AGORA

---

### 4. Cursor Command Palette

**Caminho**: Ctrl+Shift+P

**Comandos a testar**:
```
> Agents: Enable Parallel Mode
> Agents: Configure Multiple Agents
> Composer: Add Agent
> Multi-Agent: Enable
```

**Status**: TESTAR AGORA

---

### 5. Múltiplas Abas de Chat

**Teste Prático**:

**Passo 1**: Abrir nova aba de chat
- Ícone "+" no painel de chat
- Ou Ctrl+L (novo chat)

**Passo 2**: Configurar modelo diferente
- Chat 1: Claude Sonnet 4.5
- Chat 2: GPT-4 ou Codestral

**Passo 3**: Dar tarefa diferente em cada chat
- Chat 1: "Criar spec de analytics"
- Chat 2: "Criar spec de fees_taxes"

**Passo 4**: Ver se AMBOS respondem simultaneamente

**Status**: TESTAR AGORA

---

### 6. Cursor Docs Oficial

**Links para verificar**:
- https://docs.cursor.com
- https://cursor.com/features
- https://cursor.com/pricing (ver detalhes do Ultra)

**O que procurar**:
- Documentação sobre "parallel agents"
- Tutoriais de multi-agent setup
- Changelog com feature release

**Status**: VOCÊ CHECA (web browser)

---

### 7. Cursor Forum/Discord

**Comunidades**:
- Forum: https://forum.cursor.com
- Discord: Procurar por "parallel agents" ou "Ultra plan"

**Perguntas frequentes**:
- "How to enable parallel agents in Ultra?"
- "Multiple composers not working"

**Status**: VOCÊ CHECA

---

## 🎯 TESTES PRÁTICOS (Daniel Executar AGORA)

### Teste 1: Command Palette

```
1. Pressionar: Ctrl+Shift+P
2. Digitar: "agent"
3. Ver todos os comandos relacionados a "agent"
4. Copiar aqui a lista completa
```

### Teste 2: Settings Full Search

```
1. Abrir Settings (Ctrl+,)
2. Buscar: "parallel"
3. Copiar TUDO que aparecer
4. Buscar: "agent"
5. Copiar TUDO que aparecer
6. Buscar: "composer"
7. Copiar TUDO que aparecer
```

### Teste 3: Múltiplas Abas

```
1. Abrir nova aba de chat (ícone +)
2. Verificar se pode escolher modelo diferente
3. Dar tarefa diferente
4. Ver se AMBAS as abas processam ao mesmo tempo
```

---

## 📋 FORMULÁRIO DE RESULTADOS

**Daniel, preencha conforme testa**:

**Teste 1 (Command Palette "agent")**:
```
Comandos encontrados:
- [listar aqui]
```

**Teste 2 (Settings "parallel")**:
```
Configurações encontradas:
- [listar aqui]
```

**Teste 3 (Múltiplas abas)**:
```
Funcionou? SIM / NÃO
Detalhes: [descrever]
```

---

## 💡 HIPÓTESES

### Hipótese 1: Feature Ainda Não Lançada
- "Parallel agents" está na descrição do plano
- Mas feature ainda em desenvolvimento
- Será lançada em update futuro

**Como validar**: Checar changelog/roadmap

### Hipótese 2: Requer Configuração Específica
- Feature existe mas está escondida
- Precisa ativar via settings oculta
- Ou via arquivo de config (.cursor/settings.json)

**Como validar**: Buscar arquivo de config

### Hipótese 3: "Parallel" = Múltiplas Abas
- Feature já existe (múltiplas abas de chat)
- Cada aba = 1 agente
- "Parallel" = capacidade de ter várias abertas

**Como validar**: Testar múltiplas abas AGORA

---

## 🚀 AÇÃO IMEDIATA

**Daniel, faça AGORA**:

1. **Ctrl+Shift+P** → Digite "agent" → Screenshot dos resultados
2. **Settings** → Buscar "parallel" → Screenshot
3. **Nova aba de chat** (ícone +) → Tente dar tarefa → Veja se funciona

**Me mande os resultados e continuamos juntos!**

Enquanto você testa, eu preparo:
- Scripts de orquestração (se precisarmos de worktrees)
- Mapeamento de modelos por papel
- Estratégia de fallback

**Vamos descobrir isso AGORA!** 🔥

