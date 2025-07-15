from langchain_chroma import Chroma
from app.adapters.llm.ollamallm import embeddingModel

db_location = "/storage/chromaDb-wms/"

vector_store = Chroma(
    collection_name="wmsFirst",
    persist_directory=db_location,
    embedding_function=embeddingModel,
)

retriever = vector_store.as_retriever(
    search_kwargs={"k":5}
)

