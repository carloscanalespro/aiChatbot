from typing import Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

from langchain_core.messages import SystemMessage, trim_messages

from app.adapters.llm.ollamallm import llm
from app.adapters.vectorstore.vectordb import retriever


def chatTest(msg):
    #prompt template
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an information guardian and WMS consultant. Your duty is to protect sensitive data and provide accurate answers strictly within your domain: the WMS (Warehouse Management System). The user’s access level is {level}. Respect the company’s access hierarchy: Client > IT > General Staff, and deny access to information beyond the user’s role. Only answer questions related to WMS, and politely reject anything unrelated. You communicate with kindness, clarity, and precision, always responding in {language}."
                "information about wms: {info}"
                # "You are a guardian of information, your duty is protect information and provide information based on the security level people is granted"
                # "There is information about clients interface, and information about wms in general that everyone in the company have access."
                # "the access level jerarqy is client > it > general (workers). Deny any query about higher rolls"
                # "the access level of who you attending is {level}"
                # "You are an important contributor to the company your time cant be wasted for trivial stuff that has nothing todo with WMS"
                # "Please denied any question that has nothing to do with WMS"
                # "You are a great consultant of a big program called WMS a wharehouse management system, cant talk about other think because that is you job"
                # "You are a helpful assistant. Answer all questions to the best of your ability in {language}."
                # "You are kindly and pro-efficient with words"
                # "you are going to attend just questions about the matter of the WMS no more"
                # "if you are asked to do something else limit your answers to say that your purpouse it not that"
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

    #Defininf State
    class State(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        language: str
        level: str
        info: str


    #Defining Graph
    workflow = StateGraph(state_schema=State)

    def call_model(state: State):
        trimmed_messages = trimmer.invoke(state["messages"])
        prompt = prompt_template.invoke(
            {"messages": trimmed_messages, "info":state["info"], "language": state["language"], "level": state["level"]}
        )
        response = llm.invoke(prompt)
        return {"messages": [response]}

    #Defining a single node in the graph
    workflow.add_edge(START,"model")
    workflow.add_node("model", call_model)

    #adding memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    config = {"configurable": {"thread_id": "abc45678"}}
    language = "Spanish"
    accessLevel = "General Staff"
    input_messages = [HumanMessage(msg)]

    infos = retriever.invoke(msg)
    output = app.invoke(
        {
            "info": infos,
            "messages": input_messages, 
            "language": language, 
            "level":accessLevel
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