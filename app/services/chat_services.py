from typing import Sequence,Annotated, TypedDict, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

from langchain_core.messages import SystemMessage, trim_messages

from app.adapters.llm.ollamallm import llm, llm_q25

# from app.adapters.llm.ollamallm import llm_openai

from app.adapters.vectorstore.vectordb import retriever, similarity_search

from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition
from langchain_core.tools import tool

from langchain_core.output_parsers import StrOutputParser

import ast

from langchain_community.document_loaders import TextLoader


llm_search_optimizer = llm_q25
llm = llm



class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    need_search: bool
    optimized_query: list[str] | None
    current_question: str | None
    context: str | None
    response: str
    level: str
    language: str

# 1. Función modificada para decidir (ahora retorna el estado actualizado)
def decide_node(state: State) -> State:
    """Nodo que decide y actualiza el estado"""
    last_message = state["messages"][-1].content
    
    # Cargar un archivo de texto
    loader = TextLoader("demofile.txt", encoding="utf-8")
    document = loader.load()
    doclist = document[0].page_content
    
    prompt = ChatPromptTemplate.from_template("""
    You are an information guardian and WMS consultant.
    WMS has the following modules: replenishment, slam, shiping, picker, receive orders, y sus funcionalidades internas
    and has the following topics: """
    +doclist+
    """
    Your duty is to protect sensitive data and provide accurate answers strictly within your domain: the WMS (Warehouse Management System).
    You work for a important Warehouse Management System this system controls pachage and products entry, package sort, picking, packing and shipping.
    Take the all the most relevant words of the user's input for interpret what the user is talking about and output them back, you have to analyze 
    the context o situation and the pricipal action to solve some ex: i have a problem, how i delete a replenisment? output: 
    ['problem','delete','replenishment'] in this very important format: a plain text python list. if the users's request is irrelevant like:
    'what time is it?' or 'How is the weather' just ignore any request that not sounds to see with wms and return a False value in plain text no list. Return the 
    words in the current language Spanish

    original query: {query}
    optimized query: """)
    
    chain = prompt | llm_search_optimizer | StrOutputParser()
    response = chain.invoke({"query": last_message})

    print(response.center(30,"="))

    if response == 'False':
        state["need_search"] = False
        state["optimized_query"] = None
    else:
        try:
            query_terms = ast.literal_eval(response)
            state["need_search"] = True
            state["optimized_query"] = query_terms
            state["current_question"] = last_message
        except:
            state["need_search"] = False
            state["optimized_query"] = None
    
    return state  # Siempre retornamos el estado actualizado

# 2. Función de condición separada
def should_retrieve(state: State) -> Literal["retrieve", "generate"]:
    """Determina el flujo basado en el estado (no modifica estado)"""

    print("retrieve".center(30,"-") if state.get("need_search", False) else "generate".center(30,"-"))
    return "retrieve" if state.get("need_search", False) else "generate"

# 3. Nodo de recuperación modificado
def retrieve_node(state: State) -> State:
    """Recupera información y actualiza el estado"""

    # print(state["optimized_query"])
    if not state.get("optimized_query"):
        return state
    
    
    query = " ".join(state["optimized_query"])
    docs = similarity_search(query)
    state["context"] = docs  # Añadimos contexto al estado
    return state


def generate_response(state: State) -> State:
    """Genera una respuesta basada en el contexto y actualiza el estado."""
    if state.get("context"):
        # Respuesta con contexto
        prompt = ChatPromptTemplate.from_template("""
        You are an information guardian and WMS consultant. 
        Your duty is to protect sensitive data and provide accurate answers strictly within your domain: the WMS (Warehouse Management System). 
        The user’s access level is {level}. Respect the company’s access hierarchy: IT> Client > General Staff, and deny access to information beyond the user’s role. 
        Only answer questions related to WMS, and politely reject anything unrelated. 
        You communicate with kindness, clarity, and precision, always responding in {language}.
                                                  
        Use the information wisely and select the more relevant to the quesiton asked, and get the best of it to respond,
        Dont mix information
        information about wms: {context}
                
        
        Responde a la pregunta: {question}
        """)
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({
            "context": state["context"],
            "question": state["messages"][-1].content,
            "level":state["level"],
            "language":state["language"]
        })
    else:
        # Respuesta general
        prompt = ChatPromptTemplate.from_template("""
        You are an information guardian and WMS consultant. 
        Your duty is to protect sensitive data and provide accurate answers strictly within your domain: the WMS (Warehouse Management System). 
        The user’s access level is {level}. Respect the company’s access hierarchy: IT> Client > General Staff, and deny access to information beyond the user’s role. 
        Only answer questions related to WMS, and politely reject anything unrelated. 
        You communicate with kindness, clarity, and precision, always responding in {language}.
        
        Responde a la pregunta: {question}
        """)
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({
            "question": state["messages"][-1].content,
            "level":state["level"],
            "language":state["language"]
        })
    
    # Actualiza el estado con la respuesta
    state["response"] = response  # Añade esta clave al TypedDict si no existe
    return state  # Retorna el estado actualizado

# 4. Configuración corregida del grafo
workflow = StateGraph(State)

workflow.add_node("decide", decide_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_response)

workflow.add_conditional_edges(
    "decide",
    should_retrieve,  # Función que solo decide el camino
    {
        "retrieve": "retrieve",
        "generate": "generate"
    }
)

workflow.add_edge("retrieve", "generate")
workflow.set_entry_point("decide")
workflow.set_finish_point("generate")

checkpointer = InMemorySaver()
app = workflow.compile(checkpointer=checkpointer)





### WORK IN PROGRESS - (PENDING)
def chatTestWithStream(msg):
    config = {"configurable": {"thread_id": "abc789"}}
    query = "Hi I'm Todd, please tell me a joke."
    language = "English"

    input_messages = [HumanMessage(query)]
    # input_messages = messages + [HumanMessage(query)]

    return llm.stream()