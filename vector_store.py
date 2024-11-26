import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_elasticsearch import ElasticsearchStore

from config import (
    EMBEDDING_MODEL_NAME, 
    ES_URL, 
    ES_USERNAME, 
    ES_PASSWORD, 
    ES_INDEX_NAME
)
from text_processing import chunk_document

embedding = HuggingFaceBgeEmbeddings(model_name=EMBEDDING_MODEL_NAME)

elasticsearch_vector_store = ElasticsearchStore(
    index_name=ES_INDEX_NAME,
    es_url=ES_URL,
    es_user=ES_USERNAME,
    es_password=ES_PASSWORD,
    embedding=embedding,
    strategy=ElasticsearchStore.ApproxRetrievalStrategy()
)

def upload_document_to_vector_store(doc, vector_store, embedding_model):
    """
    Upload a single document chunk to the vector store.
    
    Args:
    - doc (dict): Document chunk with content and metadata
    - vector_store (ElasticsearchStore): Vector store instance
    - embedding_model: Embedding model
    """
    doc_id = doc["metadata"].get("doc_id", str(uuid.uuid4()))

    vector_store.add_texts(
        texts=[doc["page_content"]],
        metadatas=[doc["metadata"]],
        ids=[doc_id]
    )

def process_and_store_batches(documents, vector_store, batch_size=100):
    """
    Process documents in batches, chunk, embed, and store.
    
    Args:
    - documents (list): List of material documents
    - vector_store (ElasticsearchStore): Vector store instance
    - batch_size (int): Number of documents to process in a batch
    """
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]

        # Chunk documents in parallel
        chunked_documents = []
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(chunk_document, doc, idx)
                       for idx, doc in enumerate(batch)]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    chunked_documents.extend(result)

        for chunk in chunked_documents:
            upload_document_to_vector_store(
                chunk, vector_store, None
            )

        print(f"Processed, embedded, and stored batch {i // batch_size + 1}")