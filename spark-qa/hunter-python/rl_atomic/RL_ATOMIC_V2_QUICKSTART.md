#  RL ATOMIC LOOP V2 - QUICK START

## [TARGET] O QUE FOI CRIADO?

### Arquivos NOVOS (V2 - não toca no código antigo!):

1. **`flows/ultimate_platform_flow_V2.py`** [OK] JÁ EXISTE
   - Flow consertado com OAuth fix (Enter key)
   - Multi-selector fallbacks (testid → href → text → class)
   - Fuzzy validations
   - JSON output estruturado para RL

2. **`rl_atomic/golden_path_enhanced_V2.py`**  CRIADO AGORA
   - Wrapper que usa flow V2
   - Self-healing (retry + recovery paths)
   - Step-by-step tracking (cada método = 1 step)
   - Salva runs em `barril!!` automaticamente

3. **`rl_atomic/train_atomic_loop_V2.py`**  CRIADO AGORA
   - CLI trainer que gera runs usando flow V2
   - Integra com RL Atomic Loop existente
   - Processa runs (reward, select, extract, bootstrap, cleanup)

---

## [ROCKET] COMO USAR?

### 1. Teste básico (3 runs, browser visível):

```bash
cd hunter-python
python rl_atomic/train_atomic_loop_V2.py --runs 3 --no-headless
```

**O que vai acontecer:**
- [OK] Abre browser (visível)
- [OK] Executa 3 runs do flow V2 (login → properties → create_property)
- [OK] Salva cada run em `barril!!` com métricas
- [OK] Processa runs com RL Atomic Loop (reward, tier selection, patterns)
- [OK] Mostra summary com success rate, recovery rate, etc

---

### 2. Produção (10 runs, headless):

```bash
python rl_atomic/train_atomic_loop_V2.py --runs 10 --headless
```

---

### 3. Só processar barril (sem gerar runs novos):

```bash
python rl_atomic/train_atomic_loop_V2.py --process-only
```

**Útil quando:**
- Você já tem runs no `barril!!`
- Quer re-processar com novos parâmetros
- Quer testar reward calculation sem rodar browser

---

### 4. Só gerar runs (sem processar):

```bash
python rl_atomic/train_atomic_loop_V2.py --runs 5 --no-headless --no-process
```

**Útil quando:**
- Quer gerar runs rapidamente
- Vai processar depois manualmente
- Debugging do flow

---

## [CHART] O QUE O RL APRENDE?

Cada run salvo em `barril!!` contém:

```json
{
  "run_id": "run_V2_20241106_153045",
  "success": true,
  "duration": 12.5,
  "total_steps": 3,
  "success_steps": 3,
  "recovery_steps": 0,
  "failure_steps": 0,
  "has_shortcuts": false,
  "has_recovery": false,
  "steps": [
    {
      "step_num": 1,
      "action": "login",
      "status": "success",
      "duration": 4.2,
      "state_from": "login_page",
      "state_to": "dashboard",
      "actions_taken": ["fill_username", "fill_password", "press_enter"],
      "selectors_used": ["username_field", "password_field"],
      "fuzzy_validation": {"url_check": true, "testid_check": true}
    },
    {
      "step_num": 2,
      "action": "navigate_to_properties",
      "status": "success",
      "duration": 2.8,
      "state_from": "dashboard",
      "state_to": "properties_list",
      "actions_taken": ["click_dropdown", "click_properties_link"],
      "selectors_used": ["user_dropdown", "properties_link"]
    },
    {
      "step_num": 3,
      "action": "create_property",
      "status": "success",
      "duration": 5.5,
      "state_from": "properties_list",
      "state_to": "property_creation_form",
      "actions_taken": ["click_add_button", "select_property_type"],
      "selectors_used": ["add_property_button", "single_property_option"]
    }
  ],
  "flow_version": "V2"
}
```

---

##  WORKFLOW COMPLETO:

```
1. train_atomic_loop_V2.py
   ↓
2. golden_path_enhanced_V2.py
   ↓
3. ultimate_platform_flow_V2.py (métodos individuais)
   ↓
4. Salva run em barril!!
   ↓
5. atomic_loop.py processa:
   - PHASE 1: LOAD runs
   - PHASE 2: REWARD calculation
   - PHASE 2.5: RLAIF validation
   - PHASE 3: SELECT tiers (T1/T2/T3)
   - PHASE 4: EXTRACT patterns
   - PHASE 5: BOOTSTRAP memory
   - PHASE 6: CLEANUP barril
   ↓
6. RL aprende:
   - Quais selectors funcionam melhor
   - Quais actions levam a shortcuts
   - Quais recovery paths funcionam
   - Timing patterns (quanto tempo cada step leva)
```

---

## [OK] PRÓXIMOS PASSOS:

1. **Testar integração**: `python rl_atomic/train_atomic_loop_V2.py --runs 3 --no-headless`
2. **Validar runs salvos**: Checar `barril!!/*.json` pra ver se tá correto
3. **Validar RL processing**: Ver se reward, tiers, patterns foram extraídos
4. **Explorar property form**: Criar script pra mapear campos do form
5. **Implementar form filling**: Completar create_property() com preenchimento de campos

---

## [GUARD] SEGURANÇA:

- [OK] Código antigo **NÃO FOI TOCADO**
- [OK] Tudo tem **V2** no nome
- [OK] Runs salvos em `barril!!` (separado do código)
- [OK] Pode rodar em paralelo com sistema antigo
- [OK] Se der erro, basta deletar os arquivos V2

---

##  TROUBLESHOOTING:

### "Module not found: ultimate_platform_flow_V2"
```bash
# Verificar se arquivo existe:
ls flows/ultimate_platform_flow_V2.py
```

### "Cannot import GoldenPathEnhancedV2"
```bash
# Rodar de dentro de hunter-python/:
cd hunter-python
python rl_atomic/train_atomic_loop_V2.py --runs 1 --no-headless
```

### "Config not found"
```bash
# Verificar config.py:
cat config.py | grep USERNAME
# Ou editar train_atomic_loop_V2.py linha ~60 com suas credenciais
```

---

## [FOLDER] ESTRUTURA DE ARQUIVOS:

```
hunter-python/
 flows/
    ultimate_platform_flow_V2.py  [OK] Flow consertado
 rl_atomic/
    golden_path_enhanced_V2.py     Wrapper V2
    train_atomic_loop_V2.py        Trainer V2
    atomic_loop.py                 (existente - processa runs)
    reward_shaper.py               (existente - calcula rewards)
    run_selector.py                (existente - seleciona tiers)
    pattern_extractor.py           (existente - extrai patterns)
    memory_bootstrap.py            (existente - carrega memory)
    barril_cleaner.py              (existente - limpa barril)
 knowledge-machine/
    rl_core.py                     (existente - core RL)
 engines/
    fast_learner.py                (existente - learning acelerado)
 barril!!/                          (runs salvos aqui)
     run_V2_*.json                   Runs do flow V2
```

---

**[PARTY] PRONTO PRA TESTAR!**
