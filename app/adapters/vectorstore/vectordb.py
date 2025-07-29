from langchain_chroma import Chroma
from app.adapters.llm.ollamallm import embed, embeddingModel

db_location = "/storage/chromaDb-wms/"

vector_store = Chroma(
    collection_name="wmsFirst",
    persist_directory=db_location,
    embedding_function=embeddingModel,
)

retriever = vector_store.as_retriever(
    search_kwargs={"k":5}
)

def similarity_search(req:str):
    return vector_store.similarity_search(req) 

