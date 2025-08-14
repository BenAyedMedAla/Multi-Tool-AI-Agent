from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode
from typing import List, Literal
from langgraph.graph import StateGraph, MessagesState, START, END
from tools import T

tools=T
llm= ChatOllama(model="llama3.2:latest")
llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools)

def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def call_tools(state: MessagesState) -> Literal["tools", END]: # pyright: ignore[reportInvalidTypeForm]
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# initialize the workflow from StateGraph
workflow = StateGraph(MessagesState)

# add a node named LLM, with call_model function. This node uses an LLM to make decisions based on the input given
workflow.add_node("LLM", call_model)

# Add a tools node
workflow.add_node("tools", tool_node)

# Our workflow starts with the LLM node
workflow.add_edge(START, "LLM")

# Add a conditional edge from LLM to call_tools function. It can go tools node or end depending on the output of the LLM. 
workflow.add_conditional_edges("LLM", call_tools)

# tools node sends the information back to the LLM
workflow.add_edge("tools", "LLM")

agent = workflow.compile()

for chunk in agent.stream(
    {"messages": [("user", "hi there")]},
    stream_mode="values",):
    chunk["messages"][-1].pretty_print()