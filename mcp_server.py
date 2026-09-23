from mcp.server.fastmcp import FastMCP
import json

# Inicializa o servidor FastMCP
mcp = FastMCP("Database-Server")

@mcp.tool()
def get_order_details_mcp(order_id: str) -> str:
    """Ferramenta MCP para consultar dados do pedido direto do banco de dados corporativo."""
    mock_db = {
        "PED-123": {"item": "Teclado Mecânico", "valor": 250.00, "status": "Entregue"},
        "PED-456": {"item": "Mouse Gamer", "valor": 80.00, "status": "Em trânsito"}
    }
    order = mock_db.get(order_id.upper())
    if order:
        return json.dumps(order)
    return json.dumps({"error": "Pedido não encontrado no banco MCP."})

if __name__ == "__main__":
    mcp.run()