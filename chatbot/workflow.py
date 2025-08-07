from langgraph.graph import StateGraph, START,END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant")

class ChatbotState(TypedDict):
    messages:Annotated[List[BaseMessage], add_messages]
    
def chat_node(state: ChatbotState):
    messages=state["messages"]
    response=llm.invoke(messages)
    return {'messages':[response]}
    
    
checkpointer=InMemorySaver()
graph = StateGraph(ChatbotState)

graph.add_node("chat_node",chat_node)

graph.add_edge(START, "chat_node")
graph.add_edge("chat_node",END)

chatbot=graph.compile(checkpointer=checkpointer)

