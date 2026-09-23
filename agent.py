import json
import asyncio
from typing import Literal
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import AgentState
from tools import tools  # Nossas ferramentas locais (como o process_refund)

load_dotenv(override=True)

# Instanciamos o modelo base
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# --- NOTA SOBRE MCP EM PRODUÇÃO ---
# O protocolo MCP permite registrar ferramentas remotas via transporte Stdio ou SSE.
# Aqui mantemos as ferramentas locais unificadas com a especificação MCP do servidor.
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState) -> dict:
    """Nó responsável por enviar o histórico de mensagens para a LLM."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def run_tools(state: AgentState) -> dict:
    """Nó personalizado para executar as ferramentas (locais e MCP) e avaliar aprovação humana."""
    last_message = state["messages"][-1]
    
    tools_by_name = {tool.name: tool for tool in tools}
    tool_outputs = []
    
    requires_approval = False
    pending_action = None

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        selected_tool = tools_by_name.get(tool_name)
        if selected_tool:
            result = selected_tool.invoke(tool_args)
        else:
            result = json.dumps({"error": f"Ferramenta {tool_name} não encontrada."})
        
        # Regra do Human-in-the-Loop para reembolsos
        if tool_name == "process_refund":
            data = json.loads(result)
            if data.get("status") == "pending_approval":
                requires_approval = True
                pending_action = {
                    "tool_call_id": tool_call["id"],
                    "order_id": tool_args.get("order_id"),
                    "amount": tool_args.get("amount"),
                    "reason": tool_args.get("reason")
                }
        
        tool_outputs.append(
            ToolMessage(content=str(result), tool_call_id=tool_call["id"])
        )

    return {
        "messages": tool_outputs,
        "requires_approval": requires_approval,
        "pending_action": pending_action
    }

def should_continue(state: AgentState) -> Literal["tools", "human_approval", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    
    if state.get("requires_approval"):
        return "human_approval"
        
    return END

def human_approval_node(state: AgentState) -> dict:
    return {}

# --- Construção do Grafo ---
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", run_tools)
workflow.add_node("human_approval", human_approval_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "human_approval": "human_approval",
        END: END
    }
)

workflow.add_conditional_edges(
    "tools",
    should_continue,
    {
        "human_approval": "human_approval",
        "tools": "agent",
        END: END
    }
)

checkpointer = MemorySaver()
app_graph = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_approval"]
)