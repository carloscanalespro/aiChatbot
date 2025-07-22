from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings

# llm = ChatOllama(model="deepseek-r1:1.5b")
llm = ChatOllama(
    model="qwen3:0.6b",
    temperature=1.0
    )


embeddingModel = OllamaEmbeddings(model="bge-m3:latest")

# agentQwen3 = crear
