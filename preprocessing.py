from api_client import fetch_materials_data
from vector_store import elasticsearch_vector_store, process_and_store_batches

def preprocessing():
    """
    Main function to fetch materials data and store in vector database.
    """
    results = fetch_materials_data()
    
    if not results:
        print("No materials data fetched. Exiting.")
        return
    
    process_and_store_batches(
        results,
        elasticsearch_vector_store,
        batch_size=5
    )
    
    print("Materials data processing complete.")

if __name__ == "__main__":
    preprocessing()