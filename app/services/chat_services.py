from typing import Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph, Graph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

from langchain_core.messages import SystemMessage, trim_messages

from app.adapters.llm.ollamallm import llm, llm_gm3
from app.adapters.vectorstore.vectordb import retriever

from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition
from langchain_core.tools import tool

from langchain_core.output_parsers import StrOutputParser

import json


llm_search_optimizer = llm_gm3

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query:str
    question:str
    language: str
    level: str
    info: str

# 2. Función para optimizar la consulta de búsqueda
def decide_if_retrieve(user_query):
    """Usa un modelo pequeño para refinar la consulta de búsqueda"""

    prompt = ChatPromptTemplate.from_template("""
    You work for a important Warehouse Management System this system controls pachage and products entry, package sort, picking, packing and shipping.
    Take the all the most relevant words of the user's input for interpret what the user is talking about and output them back, you have to analyze 
    the context o situation and the pricipal action to solve some ex: i have a problem, how i delete a replenisment? output: 
    ['problem','delete','replenishment'] in this very important format: a plain text python list. if the users's request is irrelevant like:
    'what time is it?' or 'How is the weather' just ignore any request that not sounds to see with wms and return a False value. Return the 
    words in the current language Spanish

    original query: {query}
    
    optimized query: """)
    
    chain = prompt | llm_search_optimizer | StrOutputParser()

    response = chain.invoke({"query": user_query})
    reponse_json = json.loads(response)
    print(json.loads(response).center(40, "-"))

    return reponse_json if reponse_json != 'False' else False


def retrieve_information(state):
    """Recupera información relevante de ChromaDB"""

    query = state["messages"][-1].content
    docs = retriever.invoke(query)

    return {"context": docs, "question": query}

def generate_response(state):
    """Genera una respuesta basada en el contexto o sin él"""
    if "context" in state:
        # Respuesta con contexto
        prompt = ChatPromptTemplate.from_template("""
        Eres un asistente útil. Basándote en la siguiente información:
        {context}
        
        Responde a la pregunta: {question}
        """)
        chain = prompt | llm | StrOutputParser()
        return chain.invoke(state)
    else:
        # Respuesta general sin consultar la base de datos
        prompt = ChatPromptTemplate.from_template("""
        Eres un asistente útil. Responde a la siguiente pregunta:
        {question}
        """)
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"question": state["messages"][-1].content})

# 4. Construcción del graph
workflow = Graph()

# Agregar nodos
workflow.add_node("decide", decide_if_retrieve)
workflow.add_node("retrieve", retrieve_information)
workflow.add_node("generate", generate_response)

# Definir las conexiones
workflow.add_conditional_edges(
    "decide",
    decide_if_retrieve,
    {
        "retrieve": "retrieve",
        "generate": "generate"
    }
)
workflow.add_edge("retrieve", "generate")

# Establecer puntos de entrada y salida
workflow.set_entry_point("decide")
workflow.set_finish_point("generate")

# Compilar el graph
app = workflow.compile()


def chatTest(msg:str, userId:int):
    print(str(userId).center(10,"-"))
    config = {"configurable": {"thread_id": userId}} #Ver como se manejen solos los hilos de memoria
    language = "Spanish"
    accessLevel = "General Staff"
    input_messages = [HumanMessage(msg)]

    infos = retriever.invoke(msg) #HACER UNA TOOL o optimzar de alguna forma para que se ahorren recursos y tiempo
    output = app.invoke(
        {
            "info": infos,
            "messages": input_messages, #Verificar la eficacio del prompt
            "language": language, #Agregar el idioma segun la ubicacion del usuario
            "level":accessLevel #Coordinar el acceso con el login
        },
        config,
    )

    return output["messages"][-1]




### WORK IN PROGRESS - (PENDING)
def chatTestWithStream(msg):
    config = {"configurable": {"thread_id": "abc789"}}
    query = "Hi I'm Todd, please tell me a joke."
    language = "English"

    input_messages = [HumanMessage(query)]
    # input_messages = messages + [HumanMessage(query)]

    return llm.stream()