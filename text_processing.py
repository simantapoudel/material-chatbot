import uuid
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter

def create_material_metadata(document):
    """
    Extract and organize metadata from a material document.
    
    Args:
    - document (dict): Raw material document from API
    
    Returns:
    - dict: Structured metadata
    """
    return {
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
        "possible_species": document.get("possible_species", [])
    }

def chunk_document(document, index):
    """
    Chunk a single document and attach metadata to each chunk.
    
    Args:
    - document (dict): Material document
    - index (int): Document index
    
    Returns:
    - list: Chunked documents with metadata
    """
    try:
        document_id = str(uuid.uuid4())
        material_metadata = create_material_metadata(document)

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
        )

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        document_chunks = text_splitter.split_text(content)

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