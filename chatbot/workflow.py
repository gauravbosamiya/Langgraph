from langgraph.graph import StateGraph, START,END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
import sqlite3

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant")

class ChatbotState(TypedDict):
    messages:Annotated[List[BaseMessage], add_messages]
    
def chat_node(state: ChatbotState):
    messages=state["messages"]
    response=llm.invoke(messages)
    return {'messages':[response]}
    
    
conn=sqlite3.connect(database="chatbot.db",check_same_thread=False)    

checkpointer=SqliteSaver(conn=conn)
graph = StateGraph(ChatbotState)

graph.add_node("chat_node",chat_node)

graph.add_edge(START, "chat_node")
graph.add_edge("chat_node",END)

chatbot=graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads=set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
        
    return list(all_threads)


# CONFIG={'configurable':{'thread_id':'thread-2'}}
    
# response = chatbot.invoke(
#                 {'messages':[HumanMessage(content='what is the capital of india. Acknowledge my name while answering')]},
#                 config=CONFIG,
#             )
# print(response)
