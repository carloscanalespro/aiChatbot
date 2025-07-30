from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings

llm = ChatOllama(model="deepseek-r1:1.5b")
llm = ChatOllama(
    model="qwen3:0.6b",
    temperature=1.0
    )

llm_q25 = ChatOllama(
    model="qwen2.5:3b",
    temperature=1.0
    )

llm_gm3 = ChatOllama(
    model="gemma3:4b",
    temperature=1.0
    )


embeddingModel = OllamaEmbeddings(model="bge-m3:latest")