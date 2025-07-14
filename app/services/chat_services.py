from langchain_core.messages import AIMessage, HumanMessage
from app.agents.chat_agent import llm


def chatTest(msg):
    result = llm.invoke(
        [
            HumanMessage(content="hi I'm bob"),  
            AIMessage(content="Hello Bob! How can I assist you today?"),
            HumanMessage(content=msg)
        ]
    )
    return result

def chatTestWithStream(msg):
    config = {"configurable": {"thread_id": "abc789"}}
    query = "Hi I'm Todd, please tell me a joke."
    language = "English"

    input_messages = [HumanMessage(query)]
    # input_messages = messages + [HumanMessage(query)]


    return llm.stream()