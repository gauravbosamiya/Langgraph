from langgraph.graph import StateGraph, START,END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
import sqlite3
import requests
import os
from langchain_core.tools import tool
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b")


search_tool = DuckDuckGoSearchRun(region="us-en", name="brave_search")

@tool
def calculator(first_num:float, second_num:float, operation:str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation=="add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {'error':'Division by zero is not allowed'}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num":first_num, "second_num":second_num, "operation":operation, "result":result}
    except Exception as e:
        return {"error":str(e)}
  
@tool    
def get_stock_price(symbol:str)->dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
    using Alpha Vantage with API key in the URL.
    """
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    
    r = requests.get(url)
    return r.json()

@tool
def get_live_weather(city:str) -> dict:
    """This function fetches the current weather data for a given city""" 
    api_key = os.getenv("WEATHERSTACK_API_KEY")
    url = f"https://api.weatherstack.com/current?access_key={api_key}&query={city}"
    response = requests.get(url)
    return response.json()

tools = [get_stock_price, get_live_weather, search_tool, calculator]
llm_with_tool = llm.bind_tools(tools)

class ChatbotState(TypedDict):
    messages:Annotated[List[BaseMessage], add_messages]
    
def chat_node(state: ChatbotState):
    messages=state["messages"]
    response=llm_with_tool.invoke(messages)
    return {'messages':[response]}

tool_node = ToolNode(tools)
    
conn=sqlite3.connect(database="chatbot.db",check_same_thread=False)    
checkpointer=SqliteSaver(conn=conn)

graph = StateGraph(ChatbotState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools",tool_node)

graph.add_edge(START, "chat_node")

graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge("tools","chat_node")

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads=set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
        
    return list(all_threads)

