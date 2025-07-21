from typing import Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

from langchain_core.messages import SystemMessage, trim_messages

from app.adapters.llm.ollamallm import llm
from app.adapters.vectorstore.vectordb import retriever

#Todavia me falta el streming del prompt

#VER si el schema, template y trimmer los mando a otras carpetas y los uso como paquetes
# para que no estorben
class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str
    level: str
    info: str


prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an information guardian and WMS consultant. Your duty is to protect sensitive data and provide accurate answers strictly within your domain: the WMS (Warehouse Management System). The user’s access level is {level}. Respect the company’s access hierarchy: Client > IT > General Staff, and deny access to information beyond the user’s role. Only answer questions related to WMS, and politely reject anything unrelated. You communicate with kindness, clarity, and precision, always responding in {language}."
                "information about wms: {info}"
            ),
            MessagesPlaceholder(variable_name="messages")
        ]
    )

trimmer = trim_messages(
    max_tokens=65,
    strategy="last",
    token_counter=llm,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

def call_model(state: State):
    trimmed_messages = trimmer.invoke(state["messages"])
    prompt = prompt_template.invoke(
        {"messages": trimmed_messages, "info":state["info"], "language": state["language"], "level": state["level"]}
    )
    response = llm.invoke(prompt)
    return {"messages": [response]}


workflow = StateGraph(state_schema=State)

workflow.add_edge(START,"model")
workflow.add_node("model", call_model)

#adding memory
memory = InMemorySaver()#Ver que tipo de memoria me conviene mas
app = workflow.compile(checkpointer=memory)


def chatTest(msg):
  
    config = {"configurable": {"thread_id": "2"}} #Ver como se manejen solos los hilos de memoria
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