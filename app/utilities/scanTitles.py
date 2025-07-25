

filePath = "C:/Users/soportegnex/Documents/AiDays/documentatio/docwms/docs/"

# import glob

# file_pattern = filePath + "**/*.md"

# for file_path in glob.glob(file_pattern, recursive=True):
#     try:
#         with open(file_path, encoding="utf-8") as f:
#             for line in f:
#                 if "#" in line:
#                     with open("demofile.txt", "a", encoding="utf-8") as d:
#                         d.write(line)
    
#     except UnicodeDecodeError:
#         print(f"Error: No se pudo leer {file_path} (codificacion no valida)")

from langchain_community.document_loaders import TextLoader

# Cargar un archivo de texto
loader = TextLoader("demofile.txt", encoding="utf-8")
document = loader.load()
print(document[0].page_content)

