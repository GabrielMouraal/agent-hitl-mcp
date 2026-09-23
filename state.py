from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # O add_messages é o segredo aqui: ele diz ao LangGraph para ANEXAR
    # novas mensagens à lista existente em vez de sobrescrever tudo.
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Campo personalizado para controlar se precisamos de intervenção humana
    requires_approval: bool
    pending_action: dict | None