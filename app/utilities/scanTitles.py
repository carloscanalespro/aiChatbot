

filePath = "C:/Users/soportegnex/Documents/AiDays/documentatio/docwms/docs/"

import glob
import re

def extract_title_from_line(line: str):
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

file_pattern = filePath + "**/*.md"

for file_path in glob.glob(file_pattern, recursive=True):
    try:
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                extracted_title = extract_title_from_line(line)
                if extracted_title:
                    with open("demofile.txt", "a", encoding="utf-8") as d:
                        d.write(line)
    
    except UnicodeDecodeError:
        print(f"Error: No se pudo leer {file_path} (codificacion no valida)")
    
# from langchain_community.document_loaders import TextLoader

# # Cargar un archivo de texto
# loader = TextLoader("demofile.txt", encoding="utf-8")
# document = loader.load()
# print(document[0].page_content)

