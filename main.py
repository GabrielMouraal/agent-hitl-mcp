from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from agent import app_graph

app = FastAPI(
    title="AI Agent - Operational Support & HITL",
    description="Agente de Suporte Operacional com fluxo Human-in-the-Loop em LangGraph"
)

# Schemas dos payloads de entrada
class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    manager_reason: str | None = None

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Agente Operacional HITL no ar!"}

@app.post("/chat")
def chat(payload: ChatRequest):
    # Configuração da thread de persistência no LangGraph
    config = {"configurable": {"thread_id": payload.thread_id}}
    
    # Executa o grafo até terminar ou até bater na interrupção do HITL
    events = app_graph.invoke(
        {"messages": [HumanMessage(content=payload.message)]},
        config=config
    )
    
    # Verifica o estado atual para saber se caiu no nó de aprovação
    state_snapshot = app_graph.get_state(config)
    
    # Se 'next' contiver 'human_approval', o LangGraph pausou a execução
    if state_snapshot.next and "human_approval" in state_snapshot.next:
        pending_action = state_snapshot.values.get("pending_action")
        return {
            "status": "requires_approval",
            "message": "Ação de alto valor detectada. Aguardando aprovação do gerente.",
            "pending_action": pending_action
        }
    
    # Caso contrário, pega a resposta final do agente
    last_message = state_snapshot.values["messages"][-1]
    return {
        "status": "completed",
        "response": last_message.content
    }

@app.post("/approve")
def approve_action(payload: ApprovalRequest):
    config = {"configurable": {"thread_id": payload.thread_id}}
    
    # Pega o estado pausado
    state_snapshot = app_graph.get_state(config)
    if not state_snapshot.next or "human_approval" not in state_snapshot.next:
        raise HTTPException(status_code=400, detail="Nenhuma ação pendente de aprovação para esta thread_id.")

    if payload.approved:
        feedback_msg = f"Aprovação concedida pelo gerente. Motivo/Nota: {payload.manager_reason or 'Sem observações'}. Pode prosseguir com o reembolso."
    else:
        feedback_msg = f"Aprovação NEGADA pelo gerente. Motivo: {payload.manager_reason or 'Não informado'}. Não execute o reembolso."

    # Atualiza o estado do grafo injetando a resposta do gerente
    app_graph.update_state(
        config,
        {"messages": [HumanMessage(content=feedback_msg)]},
        as_node="human_approval"
    )

    # Retoma a execução a partir do ponto onde estava pausado
    res = app_graph.invoke(None, config=config)
    
    last_message = res["messages"][-1]
    return {
        "status": "resumed",
        "approved": payload.approved,
        "response": last_message.content
    }