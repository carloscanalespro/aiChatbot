from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings

llm = ChatOllama(model="llama3.2:3b")

embeddingModel = OllamaEmbeddings(model="bge-m3:latest")
