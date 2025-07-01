import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
# Import OpenAI LLM and Embedding
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Set your OpenAI API key here or in your .env file as OPENAI_API_KEY
# This key will be used for both the LLM (ChatGPT) and the embedding model.

# Ensure OPENAI_API_KEY is set
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Please set your OpenAI API key in a .env file or directly in the script.")
    exit()

# Configure LlamaIndex settings to use OpenAI for both LLM and embeddings
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

# Directory where your documents are stored
DOCUMENTS_DIR = "data"

def setup_document_directory():
    """Ensures the 'data' directory exists."""
    if not os.path.exists(DOCUMENTS_DIR):
        os.makedirs(DOCUMENTS_DIR)
        print(f"Created directory: '{DOCUMENTS_DIR}'")
        print("Please place your documents (e.g., .txt, .pdf) inside this 'data' directory.")
        print("Example: echo 'This is a sample document about LlamaIndex.' > data/sample.txt")
        return False
    return True

def load_documents():
    """Loads documents from the specified directory."""
    print(f"Loading documents from '{DOCUMENTS_DIR}'...")
    try:
        # SimpleDirectoryReader can read various file types (txt, pdf, docx, etc.)
        # Ensure you have the necessary dependencies installed for each type (e.g., pypdf for PDFs)
        documents = SimpleDirectoryReader(DOCUMENTS_DIR).load_data()
        if not documents:
            print(f"No documents found in '{DOCUMENTS_DIR}'. Please add some files.")
            return None
        print(f"Loaded {len(documents)} document(s).")
        return documents
    except Exception as e:
        print(f"Error loading documents: {e}")
        print("Make sure you have installed necessary libraries for your document types (e.g., 'pip install pypdf' for PDFs).")
        return None

def create_index(documents):
    """Creates a VectorStoreIndex from the loaded documents."""
    print("Creating index from documents...")
    try:
        index = VectorStoreIndex.from_documents(documents)
        print("Index created successfully.")
        return index
    except Exception as e:
        print(f"Error creating index: {e}")
        return None

def main():
    """Main function to run the RAG application."""
    print("--- LlamaIndex RAG Application (OpenAI Only) ---") # Updated title

    if not setup_document_directory():
        return # Exit if directory needs population

    documents = load_documents()
    if not documents:
        return # Exit if no documents or error loading

    index = create_index(documents)
    if not index:
        return # Exit if index creation failed

    # Create a query engine from the index
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
                    print(f"  Text (snippet): {node.text[:200]}...") # Show first 200 chars
            print("--------------")
        except Exception as e:
            print(f"An error occurred during query: {e}")
            print("Please check your OpenAI API key and internet connection, and ensure you have sufficient quota.")

if __name__ == "__main__":
    main()