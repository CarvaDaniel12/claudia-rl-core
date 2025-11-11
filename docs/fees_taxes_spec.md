# Quick Spec: Fees & Taxes Module

**Módulo**: fees_taxes  
**Versão**: 1.0  
**Data**: 2025-11-10  
**Autores**: Time RL Core (colaboração)  
**Baseado em**: FEE_MODAL_SCAN.json, scan_pricing_tab.py (projeto Spark)

---

## Visão Geral

O módulo **Fees & Taxes** gerencia criação, configuração e aplicação de taxas e impostos a propriedades no sistema Spark.

**Fonte de Verdade**: `hunter-python/flows/v3/scans_exploration/FEE_MODAL_SCAN.json`

---

## Casos de Uso (Analyst/PM)

### UC1: Criar Nova Fee/Tax

**Ator**: Usuário (property manager)  
**Pré-condição**: Logado + navegou para Pricing Tab  
**Fluxo**:
1. Clicar em "Add Fee/Tax" button
2. Preencher nome (ex: "Property Tax 2025")
3. Preencher amount (ex: 1500.00)
4. Preencher taxationRate (ex: 0.10 = 10%)
5. Escolher appliesTo: ALL_PROPERTIES ou SELECTED_PROPERTIES
6. Se SELECTED: selecionar propriedades específicas
7. Clicar em Save
8. Verificar fee criado na lista

**Pós-condição**: Fee/Tax salvo e aplicável a propriedades

**Critério de Aceitação (QA/TEA)**:
- [ ] Modal de Fee/Tax abre com campos vazios
- [ ] Todos os campos obrigatórios validados (name, amount, taxationRate)
- [ ] TaxationRate aceita valores 0.0-1.0 (0% a 100%)
- [ ] Fee salvo aparece na lista de fees ativos
- [ ] Fee aplicado corretamente a propriedades

---

### UC2: Aplicar Fee/Tax a Propriedades

**Ator**: Sistema  
**Pré-condição**: Fee/Tax criado  
**Fluxo**:
1. Sistema identifica appliesTo (ALL ou SELECTED)
2. Se ALL: aplicar a todas as propriedades ativas
3. Se SELECTED: aplicar apenas às selecionadas
4. Calcular total para cada propriedade: `total = base_price + (base_price * taxationRate) + amount`

**Pós-condição**: Fees aplicados e refletidos no preço total

**Critério de Aceitação (Architect)**:
- [ ] Aplicação a ALL_PROPERTIES cobre 100% das propriedades
- [ ] Aplicação a SELECTED_PROPERTIES respeita seleção
- [ ] Cálculo de taxa correto: `tax = base * taxationRate`
- [ ] Total final = base + tax + amount (fees fixos)

---

### UC3: Calcular Total com Múltiplas Taxas

**Ator**: Sistema (cálculo automático)  
**Pré-condição**: Propriedade tem múltiplos fees/taxes aplicados  
**Fluxo**:
1. Somar todos os `amount` (fees fixos)
2. Somar todos os `taxationRate` (percentuais)
3. Calcular: `total = base_price * (1 + sum(taxRates)) + sum(amounts)`

**Pós-condição**: Preço total calculado corretamente

**Critério de Aceitação (Dev + QA/TEA)**:
- [ ] Múltiplos fees aplicados não se sobrepõem incorretamente
- [ ] Cálculo composto de taxas correto
- [ ] Arredondamento de valores monetários (2 decimais)

---

## Pontos de Integração (Architect)

### Entrada
- **Property Module**: Base price, property selection
- **User Input**: Fee/Tax form data

### Saída
- **Analytics Module**: Eventos de FEE_CREATED, TAX_CALCULATED
- **Property Module**: Total price atualizado

### Contratos
- `contracts/fees_taxes_schema.json`: Estrutura de fee/tax
- `contracts/fees_taxes_interface.json`: API entre módulos

---

## Dados de Teste (Dev)

### Cenário 1: Fee Simples

```json
{
  "name": "Property Tax 2025",
  "amount": 1500.00,
  "taxationRate": 0.10,
  "appliesTo": "ALL_PROPERTIES"
}
```

**Expected**:
- Fee criado com ID único
- Aplicado a todas as propriedades
- Para base_price = 10000: total = 10000 * 1.10 + 1500 = 12500

---

### Cenário 2: Tax Apenas (Sem Fee Fixo)

```json
{
  "name": "Sales Tax",
  "amount": 0,
  "taxationRate": 0.08,
  "appliesTo": "SELECTED_PROPERTIES"
}
```

**Expected**:
- Tax aplicado apenas a propriedades selecionadas
- Para base_price = 5000: total = 5000 * 1.08 = 5400

---

## Selectors Estáveis (QA/TEA + Architect)

**Navegação**:
- `[data-testid="property-settings-tab-pricing"]` - Pricing tab
- `.dropdown-toggle` → `text=Propriedades` - Menu de properties

**Modal de Fee**:
- `[data-testid="name"]` - Nome do fee
- `[data-testid="amount"]` - Valor fixo
- `[data-testid="fee.taxationRate"]` - Taxa percentual
- `[id="appliesTo-allProperties"]` - Radio ALL
- `[id="appliesTo-selectedProperties"]` - Radio SELECTED

**Waits Semânticos**:
```python
page.wait_for_load_state("networkidle", timeout=10000)
page.get_by_test_id("fee-modal").is_visible(timeout=5000)
```

---

## Métricas e Observability (Data-Specialist)

### Eventos a Rastrear

```json
// FEE_CREATED
{
  "type": "FEE_CREATED",
  "actor": "Data-Specialist",
  "payload": {
    "fee_id": "fee_001",
    "name": "Property Tax 2025",
    "amount": 1500.00,
    "taxationRate": 0.10,
    "appliesTo": "ALL_PROPERTIES"
  }
}

// TAX_CALCULATED
{
  "type": "TAX_CALCULATED",
  "payload": {
    "base_price": 10000,
    "tax_rate": 0.10,
    "tax_amount": 1000,
    "fee_amount": 1500,
    "total": 12500
  }
}
```

### Métricas de Run

- `fees_created_count`: Total de fees criados no run
- `tax_calculation_accuracy`: % de cálculos corretos
- `selector_success_rate`: % de selectors encontrados
- `fee_application_success`: % de aplicações bem-sucedidas

---

## Reward Calibration (Reward-Tuner)

**Perfil específico fees_taxes**:

```json
{
  "α": 0.45,
  "β": 0.25,
  "γ": 0.20,
  "δ": 0.10,
  "p": -0.60,
  "critical_assertions": [
    "tax_calculation_correct",
    "fee_applied_to_all_properties"
  ]
}
```

**Justificativa**:
- α alto (0.45): Cálculo financeiro precisa estar correto
- p severo (-0.60): Erro em dinheiro é grave
- β reduzido (0.25): Fluxo conhecido (menos exploração)

---

## Cobertura e Exploração (Coverage-Mapper)

### Rotas Alvo (Prioridade)

**Alta Prioridade**:
1. Login → Properties → Pricing → Add Fee (ALL) → Save
2. Login → Properties → Pricing → Add Tax (SELECTED) → Save

**Média Prioridade**:
3. Edit existing fee
4. Delete fee

**Baixa Prioridade (Edge Cases)**:
5. TaxRate = 0 (sem taxa)
6. TaxRate = 1.0 (100% taxa)
7. Negative amount (erro esperado)

### Cobertura Esperada

**Inicial**: 0% (módulo novo)  
**Alvo Fase 1**: 60% (happy paths)  
**Alvo Fase 2**: 80% (+ alternative paths)  
**Alvo Final**: 90% (+ edge cases)

---

## Entregáveis (Dev)

1. `contracts/fees_taxes_schema.json` - Schema de fee/tax
2. `contracts/fees_taxes_interface.json` - Contratos de API
3. `contracts/fees_taxes_test_flow.json` - Fluxos de teste
4. `docs/fees_taxes_impl.md` - Documentação de implementação
5. `reports/fees_taxes_qa.md` - Relatório de QA (após testes)

---

## Riscos (Tech-Lead + QA/TEA)

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Cálculo de taxa incorreto | Baixo | CRÍTICO | Assertions rigorosos + testes com valores conhecidos |
| Selector do modal muda | Médio | Alto | Usar data-testid (estáveis), não CSS |
| Timeout ao carregar pricing tab | Médio | Médio | wait_for_load_state("networkidle") + timeout 10s |
| Aplicação a SELECTED não funciona | Baixo | Alto | Testar ambos os fluxos (ALL e SELECTED) |

---

**Aprovação Colaborativa**:
- Analyst/PM: Aprovado (casos de uso claros)
- Architect: Aprovado (selectors estáveis, integrações mapeadas)
- Dev: Aprovado (implementável em paths permitidos)
- QA/TEA: Aprovado (critérios testáveis)
- Data-Specialist: Aprovado (métricas rastreáveis)
- Reward-Tuner: Aprovado (calibração adequada)
- Coverage-Mapper: Aprovado (rotas priorizadas)

**Próximo passo**: Tech-Lead valida DoR

