import os
import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_elasticsearch import ElasticsearchStore
from dotenv import load_dotenv
import logging
import requests

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

url = "https://api.materialsproject.org/materials/summary?_all_fields=true&_limit=100"

headers = {
    "X-API-KEY": os.getenv("MATERIAL_PROJECT_API_KEY"),
    "Cookie": "_csrf_token=authenticated; mp-session=pO59-bw1vxlh_wBq_hatmA|1733518522|mpRvqbXER0vtDcj3TqJ-RVhq5Wc",
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

results = data['data']

es_url = os.getenv("ELASTICSEARCH_URL")
es_user = os.getenv("ELASTICSEARCH_USERNAME")
es_password = os.getenv("ELASTICSEARCH_PASSWORD")
index_name = "chatbot_data"

model_name = "sentence-transformers/all-mpnet-base-v2"
embedding = HuggingFaceBgeEmbeddings(
            model_name=model_name
            )

vector_store = ElasticsearchStore(
    index_name=index_name,
    es_url=es_url,
    es_user=es_user,
    es_password=es_password,
    embedding=embedding,
    strategy=ElasticsearchStore.ApproxRetrievalStrategy()
)

def chunk_document(document, index):
    """
    Chunk a single document and attach metadata to each chunk.
    """
    try:
        document_id = str(uuid.uuid4())

        material_metadata = {
            "formula": document.get("formula_pretty", "N/A"),
            "composition": document.get("composition", {}),
            "density": document.get("density", "N/A"),
            "symmetry": document.get("symmetry", {}).get("crystal_system", "N/A"),
            "space_group": document.get("symmetry", {}).get("symbol", "N/A"),
            "material_id": document.get("material_id", "N/A"),
            "band_gap": document.get("band_gap", "N/A"),
            "is_stable": document.get("is_stable", "N/A"),
            "formation_energy_per_atom": document.get("formation_energy_per_atom", "N/A"),
            "energy_above_hull": document.get("energy_above_hull", "N/A"),
            "magnetic_properties": {
                "is_magnetic": document.get("is_magnetic", False),
                "total_magnetization": document.get("total_magnetization", 0),
                "num_magnetic_sites": document.get("num_magnetic_sites", 0),
            },
            "elements": document.get("elements", []),
            "chemsys": document.get("chemsys", "N/A"),
            "volume": document.get("volume", "N/A"),
            "structure": document.get("structure", {}).get("lattice", {}).get("matrix", []),
            "possible_species": document.get("possible_species", []),
            "xas_spectra": document.get("xas_spectra", []),
            "database_ids": document.get("database_IDs", {}),
            "provenance": document.get("origins", []),
        }

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        xas_spectra_text = ', '.join(
            f"{xas.get('edge')} edge for {xas.get('absorbing_element')}"
            for xas in document.get('xas_spectra', [])
        )

        provenance_text = ', '.join(
            f"{origin.get('name')} Last Updated: {origin.get('last_updated')}"
            for origin in document.get('origins', [])
        )

        content = (
            f"Formula: {document.get('formula_pretty', 'N/A')}, "
            f"Composition: {document.get('composition', {})}, "
            f"Density: {document.get('density', 'N/A')}, "
            f"Symmetry: {document.get('symmetry', {}).get('crystal_system', 'N/A')}, "
            f"Space Group: {document.get('symmetry', {}).get('symbol', 'N/A')}, "
            f"Material ID: {document.get('material_id', 'N/A')}, "
            f"Band Gap: {document.get('band_gap', 'N/A')}, "
            f"Stability: {'Stable' if document.get('is_stable', False) else 'Unstable'}, "
            f"Formation Energy per Atom: {document.get('formation_energy_per_atom', 'N/A')} eV, "
            f"Energy Above Hull: {document.get('energy_above_hull', 'N/A')} eV, "
            f"Magnetic Properties: {'Magnetic' if document.get('is_magnetic', False) else 'Non-Magnetic'}, "
            f"Total Magnetization: {document.get('total_magnetization', 0)} μB, "
            f"Number of Magnetic Sites: {document.get('num_magnetic_sites', 0)}, "
            f"Elements: {', '.join(document.get('elements', []))}, "
            f"Chemical System: {document.get('chemsys', 'N/A')}, "
            f"Volume: {document.get('volume', 'N/A')} Å³, "
            f"Lattice Structure: {document.get('structure', {}).get('lattice', {}).get('matrix', 'N/A')}, "
            f"Possible Species: {', '.join(document.get('possible_species', []))}, "
            f"XAS Spectra: {xas_spectra_text}, "
            f"Database IDs: {document.get('database_IDs', 'N/A')}, "
            f"Provenance: {provenance_text}"
        )

        document_chunks = text_splitter.split_text(content)
        print(document_chunks)

        chunked_documents = []
        for chunk in document_chunks:
            chunk_id = str(uuid.uuid4())
            chunked_document = {
                "page_content": chunk,
                "metadata": {
                    'doc_id': str(uuid.uuid4()),
                    'document_id': document_id,
                    'chunk_id': chunk_id,
                    **material_metadata
                }
            }
            chunked_documents.append(chunked_document)
        return chunked_documents

    except Exception as e:
        logging.error(f"Error processing document at index {index}: {e}")
        return []

from concurrent.futures import ProcessPoolExecutor, as_completed
def process_and_store_batches(documents, embedding_model, vector_store, index_name, es_url, es_user, es_password, batch_size=100):
    """
    Process documents in batches, chunk, embed, and store each batch.
    """
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]

        #Chunk documents in parallel
        chunked_documents = []
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(chunk_document, doc, idx)
                       for idx, doc in enumerate(batch)]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    chunked_documents.extend(result)

        print(chunked_documents)
        for chunk in chunked_documents:
            # Upload to vector store with embedding
            upload_document_to_vector_store(
                chunk, vector_store, embedding_model
            )

        print(f"Processed, embedded, and stored batch {i // batch_size + 1}")

def upload_document_to_vector_store(doc, vector_store, embedding_model):
    """
    Upload a single document chunk to the vector store with embedding and metadata.
    """

    doc_with_embedding = {
        "content": doc["page_content"],
        "metadata": {
            **doc["metadata"],
        },
    }

    doc_id = doc["metadata"].get("doc_id", str(uuid.uuid4()))

    print(f"Uploading document with ID {doc_id}: {doc_with_embedding}")

    #Add the document along with its embeddings to the vector store
    vector_store.add_texts(
        texts=[doc_with_embedding["content"]],
        metadatas=[doc_with_embedding["metadata"]],
        ids=[doc_id]
    )

if __name__ == "__main__":
    process_and_store_batches(
        results,
        embedding,
        vector_store,
        index_name,
        es_url,
        es_user,
        es_password,
        batch_size=5
    )