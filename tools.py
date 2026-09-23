from langchain_core.tools import tool
import json

@tool
def get_order_status(order_id: str) -> str:
    """Consulta o status e os detalhes de um pedido pelo ID."""
    # Simulando um banco de dados de pedidos
    mock_orders = {
        "PED-123": {"status": "Entregue", "item": "Teclado Mecânico", "valor": 250.00},
        "PED-456": {"status": "Em trânsito", "item": "Mouse Gamer", "valor": 80.00},
    }
    
    order = mock_orders.get(order_id.upper())
    if order:
        return json.dumps(order)
    return json.dumps({"error": "Pedido não encontrado."})

@tool
def process_refund(order_id: str, amount: float, reason: str) -> str:
    """
    Solicita o processamento de um reembolso para um pedido.
    Se o valor for superior a R$ 100,00, a ação requer aprovação prévia.
    """
    # Apenas retornamos a intenção de reembolso formatada.
    # O nó no LangGraph vai ler este resultado para decidir se pausa o fluxo ou executa direto.
    return json.dumps({
        "status": "pending_approval" if amount > 100.0 else "executed",
        "order_id": order_id,
        "amount": amount,
        "reason": reason
    })

# Lista de ferramentas disponíveis para o agente
tools = [get_order_status, process_refund]