__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
import chromadb


load_dotenv()


openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Please set your OpenAI API key in a .env file or directly in the script.")
    exit()


Settings.llm = OpenAI(
    model="gpt-3.5-turbo", 
    api_key=openai_api_key,
    temperature=0.7 
)

Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-ada-002", 
    api_key=openai_api_key
)

Settings.chunk_size = 1024 
Settings.chunk_overlap = 20 


DOCUMENTS_DIR = "data"
CHROMA_DB_PATH = "./chroma_db"

def setup_document_directory():
    """Ensures the 'data' directory exists."""
    if not os.path.exists(DOCUMENTS_DIR):
        os.makedirs(DOCUMENTS_DIR)
        print(f"Created directory: '{DOCUMENTS_DIR}'")
        return False 
    elif not os.listdir(DOCUMENTS_DIR):
        print(f"The '{DOCUMENTS_DIR}' directory is empty.")
        return False 
    print(f"Using documents from '{DOCUMENTS_DIR}'.")
    return True

def load_documents():
    """Loads documents from the specified directory."""
    print(f"Loading documents from '{DOCUMENTS_DIR}'...")
    try:
        documents = SimpleDirectoryReader(DOCUMENTS_DIR).load_data()
        if not documents:
            print(f"No documents found in '{DOCUMENTS_DIR}'. Please add some files.")
            return None
        print(f"Loaded {len(documents)} document(s).")
        return documents
    except Exception as e:
        print(f"Error loading documents: {e}")
        return None

def create_index(documents):

    print("Setting up ChromaDB client...")
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    chroma_collection = db.get_or_create_collection("gazette_rag_collection")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print("Creating or loading index from ChromaDB...")
    try:
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        print("Index created/loaded successfully.")
        return index
    except Exception as e:
        print(f"Error creating/loading index: {e}")
        return None

def main():
    
    print("--- Sri Lanka Gazette AI Analyst (Local Files & RAG with ChromaDB) ---")
    if not setup_document_directory():
        return

    documents = load_documents()
    if not documents:
        return

    index = create_index(documents)
    if not index:
        return

    query_engine = index.as_query_engine()

    print("\n--- Ready to answer your questions! ---")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        query = input("\nEnter your query: ")
        if query.lower() in ["exit", "quit"]:
            print("Exiting application. Goodbye!")
            break

        if not query.strip():
            print("Query cannot be empty. Please enter a question.")
            continue

        try:
            print("Searching for answer...")
            response = query_engine.query(query)
            print("\n--- Answer ---")
            print(response.response)
            if response.source_nodes:
                print("\n--- Sources ---")
                for i, node in enumerate(response.source_nodes):
                    print(f"Source {i+1}:")
                    print(f"  File: {node.metadata.get('file_name', 'N/A')}")
                    print(f"  Page Label: {node.metadata.get('page_label', 'N/A')}")
                    print(f"  Text (snippet): {node.text[:200]}...")
            print("--------------")
        except Exception as e:
            print(f"An error occurred during query: {e}")

if __name__ == "__main__":
    main()