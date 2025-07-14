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