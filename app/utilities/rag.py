import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.adapters.vectorstore.vectordb import vector_store

from functools import partial

# vector_store.delete_collection()


ragDirectory = "C:/Users/soportegnex/Documents/AiDays/documentatio/docwms/docs"


# from langchain_text_splitters import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    add_start_index=True
)


db_location = "./chroma_langchain_db"
add_documents = not os.path.exists(db_location)

utf8_loader = partial(TextLoader, encoding="utf-8")

if add_documents:
    # Carga el archivo markdown
    loader = DirectoryLoader(ragDirectory, glob="**/*.md", loader_cls=utf8_loader)
    docs = loader.load()
    chunks = splitter.split_documents(docs)

    vector_store.add_documents(documents=chunks)


