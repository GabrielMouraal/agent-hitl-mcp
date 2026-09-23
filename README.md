# 🤖 Autonomous AI Agent with Human-in-the-Loop (HITL) & MCP Integration

Um agente autônomo de suporte operacional e processamento de pedidos construído com **LangGraph**, **FastAPI** e **Model Context Protocol (MCP)**. 

O sistema orquestra decisões complexas de negócios, integrando verificações de segurança que **interrompem dinamicamente a execução (Human-in-the-Loop)** para ações sensíveis de alto valor financeiro antes de persistir o resultado no estado.

---

## 🎯 Problema de Negócio & Arquitetura

Sistemas autônomos baseados em LLMs precisam de limites claros para evitar ações indesejadas em ambientes de produção. Este projeto resolve esse desafio implementando um fluxo de auditoria humana baseada em regras:

1. **Atendimento Autônomo:** O agente responde dúvidas, consulta status de pedidos e processa reembolsos de até **R$ 100,00** de forma 100% automática.
2. **Interrupção Guardrail (HITL):** Caso o valor do reembolso ultrapasse **R$ 100,00**, o fluxo do LangGraph aciona um *breakpoint* automático no nó `human_approval`.
3. **Persistência de Estado:** A execução é congelada e o estado do grafo é salvo via `MemorySaver` utilizando uma `thread_id` única.
4. **Retomada Assíncrona via API:** Através de um endpoint FastAPI (`/approve`), um supervisor humano pode aprovar ou rejeitar a ação, descongelando o fluxo para finalização.

---

## 🛠️ Tecnologias e Frameworks

- **LangGraph:** Orquestração de grafos de estado ciclo-a-ciclo, controle de fluxo condicional e suporte nativo a *checkpoints* e interrupções (HITL).
- **FastAPI & Uvicorn:** API REST assíncrona para expor os endpoints de chat e de aprovação gerencial.
- **OpenAI GPT-4o-mini:** Modelo base para raciocínio e chamada estruturada de ferramentas (*Function Calling*).
- **Model Context Protocol (MCP):** Padrão aberto de arquitetura para desacoplamento de ferramentas e conexões a bancos de dados externos.
- **Pydantic & Python-dotenv:** Validação de tipos, esquemas de entrada e gestão de variáveis de ambiente.

---

## 🏗️ Estrutura do Projeto

```text
agent-hitl-mcp/
├── app/
│   ├── __init__.py
│   ├── main.py          # Endpoints FastAPI (/chat e /approve)
│   ├── agent.py         # Construção do StateGraph, Nós e Breakpoints
│   ├── state.py         # Definição das estruturas do Estado (TypedDict)
│   └── tools.py         # Ferramentas registradas (Function Calling)
├── mcp_server.py        # Servidor de ferramentas no padrão MCP
├── .env                 # Configurações de API Key
└── requirements.txt     # Dependências do projeto