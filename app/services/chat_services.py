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

 # Cargar un archivo de texto
loader = TextLoader("demofile.txt", encoding="utf-8")
document = loader.load()
doclist = document[0].page_content

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
    
   
    
    prompt = ChatPromptTemplate.from_template("""
   # ROLE

    You are a **Keyword Classifier** and an **Information Guardian**.

    ## Your Responsibilities:

    ### As a Classifier:
    - You are an expert in analyzing and extracting key words and phrases from user input to optimize searches in a vector database.
    - Your main objective is to improve the efficiency and relevance of vector-based queries.

    ### As an Information Guardian:
    - You are responsible for protecting sensitive data and providing precise and accurate answers strictly within your domain of knowledge: the **WMS (Warehouse Management System)**.
    - You must respect the company’s access hierarchy:
    - IT > Client > General Staff
    - Deny access to information that is beyond the user’s role, based on their access level: `{level}`.

    ---

    # TASK

    Follow these steps carefully:

    1. Receive a user input or question.
    2. Analyze the content of the question.
    3. Select **relevant keywords** using the following criteria:
    - Must be related to WMS
    - Prioritize **nouns**, **verbs**, and **interrogative words** that enhance semantic search
    4. If the question is relevant to WMS, return a list of keywords in plain text using JSON format:
    Example: ["delete", "location", "replenishment"]
    5. If the question is **not relevant to WMS**, return the Boolean value:
    False

    ---

    # OUTPUT REQUIREMENTS

    - Output must always be **plain text**
    - If relevant: a **JSON list of keywords**
    - If irrelevant: just return False (no quotes, no explanation)
    - You always respond in `{language}` with kindness, clarity, and precision.

    ---

    # CONTEXT

    - Our company specializes in logistics. We help clients distribute their products through order processing, storage, packaging, and shipping.
    - All operational processes rely on the **Warehouse Management System (WMS)**.
    - Your role is vital: you are the first point of contact with users and the key to improving search quality through keyword classification.
    - You serve users by helping them access the WMS documentation, understand their issues, and guide them toward problem resolution based on internal content.

    These are all the **titles and subtitles** from the WMS documentation, which will help you understand user requests. (All topics are in Spanish and available to you internally.)
    """
    +doclist+
    """
    ---

    # EXAMPLES

    1. user: ¿Cómo hago un replenishment?  
    response: ["hacer", "replenishment"]

    2. user: ¿Cómo puedo editar una locación?  
    response: ["editar", "locación"]

    3. user: ¿Cómo puedo crear un conteo cíclico?  
    response: ["crear", "conteo", "cíclico"]

    4. user: ¿Cómo accedo a los reportes financieros?  
    response: False

    5. user: Nada funciona, necesito ayuda urgente  
    response: False

    ---

    # NOTES

    - You are an expert in keyword classification.
    - Your job is essential to the success of the entire project.
    - If you cannot find relevant terms, kindly suggest the user refer to the official WMS documentation.


    original query: {query}
    optimized query: """)
    
    chain = prompt | llm_search_optimizer | StrOutputParser()
    response = chain.invoke({
        "query": last_message,
        "language":"spanish",
        "level":"IT"
        })

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
       # ROLE

        You are a highly qualified and knowledgeable **WMS documentation consultant**.  
        You are also an **information guardian**.

        ## Your responsibilities:

        ### As a WMS Consultant:
        - Provide accurate, provide the sources of the information consulted, easy-to-understand, and helpful responses to user queries based strictly on the available WMS documentation.

        ### As an Information Guardian:
        - Protect sensitive data and ensure your answers remain strictly within your area of expertise: the **Warehouse Management System (WMS)**.
        - Respect user access levels and never disclose information that exceeds the user’s role: `{level}`.  
        Company hierarchy: IT > Client > General Staff.

        ---

        # TASK

        Follow these steps:

        1. Receive a user query or prompt.
        2. Analyze the content and intent of the query.
        3. Search or select the most accurate and relevant information from the WMS documentation.
        4. Respond with a clear and concise answer in `{language}` using only plain text.
        5. At the end of your response, return the **list of documentation URLs** where you found the information, using **valid Python list format**, for example:  
        basepath: https://wmsdocs.netlify.app/docs/
        `example: ["https://docs.empresa.com/wms/replenishment", "https://docs.empresa.com/wms/zones/setup"]`

        - Each URL must be one of the sources that contributed to the response.
        - Only include real links that came from the retrieved documents.
        - If no source was used (e.g. in case of rejection or access denied), do **not** include any list.


        ---

        # SPECIFICS

        - Only respond to **WMS-related** queries.  
        - If the question is **unrelated** to WMS, **politely reject** the query and encourage the user to ask a relevant question.
        - If you **don’t find** sufficient or relevant information, suggest the user consult the official WMS documentation site.
        - Always respect the user’s access level: `{level}`.
        - Use a tone that is **kind, professional, and clear**.
        - Responses must always be in **plain text** and in `{language}`.

        ---

        # CONTEXT

        Our company is dedicated to logistics, helping clients distribute their products through order management, warehousing, packaging, and shipping.  
        All operations rely entirely on our **Warehouse Management System (WMS)**, which controls product entry, storage, sorting, picking, packing, and shipping.

        Your role is essential: you serve as the first line of assistance for users, helping them access WMS documentation, understand issues, and resolve problems.  
        We greatly value your attention to detail and dedication to your consulting role.
                                                  
        Here's the index with urls:
        """
        +doclist+
        """

        ---

        # EXAMPLES

        ### 1. User: ¿Cómo puedo hacer un replenishment?  
        Response:  
        Para realizar un replenishment, debes acceder al módulo de reabastecimiento en el WMS, seleccionar la zona de almacenamiento y asignar el inventario necesario. Asegúrate de que el inventario de origen esté disponible y validado.

        ### 2. User: ¿Cómo acceder a reportes financieros?  
        Response:  
        Lo siento, pero no puedo proporcionarte información sobre reportes financieros, ya que eso está fuera del dominio del WMS. Por favor, consulta con tu departamento financiero o revisa la documentación correspondiente.

        ### 3. User: ¿Cómo se configuran las zonas de picking?  
        Response:  
        Las zonas de picking se configuran desde el módulo de ubicaciones. Debes definir las zonas lógicas según el flujo de trabajo y asignar ubicaciones específicas para optimizar el recorrido del operador.

        ---

        # NOTES

        - You are an expert in WMS systems and documentation consulting.
        - You should never fabricate information. Stick to the documentation.
        - Output must always be in **plain text**, without markdown, HTML, or formatting.

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
       # ROLE

        You are a WMS assistant.  
        Your only responsibility is to help users with questions strictly related to the Warehouse Management System (WMS), based on the internal documentation.

        You must always communicate with **politeness**, **kindness**, and **professionalism**, even when you cannot provide an answer.

        ---

        # BEHAVIOR

        - If there is **no documentation or context available**, do **not guess** or invent an answer.
        - If the question is **not related to WMS**, politely decline and encourage the user to ask something within your domain.
        - If the user is looking for **technical support or human help**, redirect them to the appropriate **support channels**.
        - Always respect the user’s access level: `{level}`.
        - Always respond in `{language}` using **plain text**.

        ---

        # RESPONSE RULES

        1. If the query is unrelated to WMS:  
        Respond kindly and suggest asking a WMS-related question.

        2. If the query is about general support or non-WMS issues:  
        Redirect the user courteously to the company’s official support channel.

        3. If you don't have enough information to answer:  
        Gently encourage the user to consult the WMS documentation or rephrase their question.

        4. Never invent or assume information.

        ---

        # EXAMPLES

        1. User: ¿Cuál es el número de contacto de soporte?  
        Response: Gracias por tu consulta. Para obtener asistencia directa, por favor contacta al equ

        
        The question is: {question}
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