# MCP Setup Manual - Executar AGORA

**Execute estes comandos no PowerShell/Terminal**

---

## 1. Verificar Ollama Rodando

```powershell
# Testar se Ollama está acessível
curl http://localhost:11434/api/tags

# Se não responder, iniciar Ollama:
# (Windows: abrir Ollama app ou executar ollama serve)
```

**Esperado**: JSON com lista de modelos

---

## 2. Baixar Modelo de Embeddings

```powershell
ollama pull nomic-embed-text
```

**Tempo estimado**: 1-2 min (~300MB download)

**Validar**:
```powershell
ollama list
# Deve mostrar: nomic-embed-text
```

---

## 3. Criar Venv Dedicado para MCP

```powershell
cd C:\Users\User\Desktop\CLAUDIAOV3

# Criar venv
python -m venv .venv-mcp

# Ativar
.venv-mcp\Scripts\activate

# Instalar deps
python -m pip install --upgrade pip
pip install fastmcp jsonschema requests
```

---

## 4. Verificar/Atualizar .cursor/mcp.json

**Localização**: `C:\Users\User\.cursor\mcp.json`  
(você já está na pasta certa, é o arquivo "mcp" na lista)

**Conteúdo necessário**:
```json
{
  "mcpServers": {
    "claudiao-v3": {
      "command": "C:\\Users\\User\\Desktop\\CLAUDIAOV3\\.venv-mcp\\Scripts\\python.exe",
      "args": ["C:\\Users\\User\\Desktop\\CLAUDIAOV3\\tools\\claudiao_mcp_server.py"],
      "env": {
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_NUM_PARALLEL": "1",
        "OLLAMA_EMBEDDING_MODEL": "nomic-embed-text"
      }
    }
  }
}
```

**Após editar**: Reload Window no Cursor (Ctrl+Shift+P → "Developer: Reload Window")

---

## 5. Smoke Test MCP

No Cursor, abrir painel MCP e executar:

```
# Listar alvos
list_targets

# Echo test
echo text="MCP funcionando!"
```

**Esperado**: Echo retorna "MCP funcionando!"

---

## ✅ Confirmar Conclusão

Após executar os 5 passos, responda aqui:
- **"FASE 0 COMPLETA"** se tudo funcionou
- **Copie erros** se algo falhar

---

**Aguardando sua confirmação para prosseguir com FASE 1 (Binding)...**

