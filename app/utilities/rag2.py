from langchain_core.documents import Document
import os
import re
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from functools import partial
from typing import List, Dict, Optional

from app.adapters.vectorstore.vectordb import vector_store

# Configuración inicial
file_path = "C:/Users/soportegnex/Documents/AiDays/documentatio/docwms/docs"
db_location = "./chroma_langchain_db"
add_documents = not os.path.exists(db_location)

# Configuración del splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    add_start_index=True
)

# Cargador de documentos con manejo UTF-8
utf8_loader = partial(TextLoader, encoding="utf-8")
loader = DirectoryLoader(file_path, glob="**/*.md", loader_cls=utf8_loader, show_progress=True)
docs = loader.load()

def extract_title_from_line(line: str) -> Optional[str]:
    """Extrae el título de una línea Markdown o del patrón 'title:'"""
    line = line.strip()
    
    # Caso 1: Título Markdown (## Titulo)
    md_match = re.match(r'^#+\s+(.+)$', line)
    if md_match:
        return md_match.group(1).strip()
    
    # Caso 2: Patrón title: Titulo
    title_match = re.match(r'^title:\s*(.+)$', line, re.IGNORECASE)
    if title_match:
        return title_match.group(1).strip()
    
    return None

def process_markdown_file(file_path: str) -> List[Document]:
    """Procesa un archivo Markdown y devuelve documentos estructurados"""
    documents = []
    current_title = "Sin título"
    current_content = ""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Extraer título si existe en la línea
                extracted_title = extract_title_from_line(line)
                if extracted_title:
                    # Si encontramos un nuevo título, guardamos el contenido anterior
                    if current_content:
                        documents.append(create_document(current_content, current_title, file_path))
                        current_content = ""
                    current_title = extracted_title
                
                current_content += line
            
            # Añadir el último fragmento del documento
            if current_content:
                documents.append(create_document(current_content, current_title, file_path))
                
    except Exception as e:
        print(f"Error procesando {file_path}: {str(e)}")
    
    return documents

def create_document(content: str, title: str, file_path: str) -> Document:
    """Crea un Document de LangChain con metadata estructurada"""
    return Document(
        page_content=content,
        metadata={
            "title": title,
            "source": os.path.basename(file_path),
            "document_type": "section",
            "file_path": file_path
        }
    )

# Procesamiento principal
all_documents = []
for doc in docs:
    file_docs = process_markdown_file(doc.metadata['source'])
    all_documents.extend(file_docs)

# Indexación en ChromaDB
if add_documents and all_documents:
    # Dividir los documentos antes de indexar
    split_docs = splitter.split_documents(all_documents)
    
    # Crear o actualizar la base de datos vectorial
    vector_store.add_documents(
        documents=split_docs,
    )
