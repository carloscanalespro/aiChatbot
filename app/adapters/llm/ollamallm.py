from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings

# llm = ChatOllama(model="deepseek-r1:1.5b")
# llm = ChatOllama(
#     model="qwen3:0.6b",
#     temperature=1.0
#     )

# llm_q25 = ChatOllama(
#     model="qwen2.5:3b",
#     temperature=1.0
#     )

# llm_gm3 = ChatOllama(
#     model="gemma3:4b",
#     temperature=1.0
#     )


embeddingModel = OllamaEmbeddings(model="bge-m3:latest")


# import getpass
# import os

# # 
# if not os.environ.get("GOOGLE_API_KEY"):
#   os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# from langchain.chat_models import init_chat_model

# llm_gemini2 = init_chat_model("gemini-2.0-flash", model_provider="google_genai")




# os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# from langchain.chat_models import ChatOpenAI

# llm_openai = ChatOpenAI(model="gpt-4o-mini", temperature=0)  # O "gpt-3.5-turbo"


# from langchain.embeddings import OpenAIEmbeddings

# embed = OpenAIEmbeddings(
#     model="text-embedding-3-small",
# )
