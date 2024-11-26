import requests
from config import (
    MATERIAL_PROJECT_URL, 
    MATERIAL_PROJECT_API_KEY, 
    logger
)

def fetch_materials_data():
    """
    Fetch materials data from Materials Project API.
    
    Returns:
    - List of material dictionaries or None if fetch fails
    """
    headers = {
        "X-API-KEY": MATERIAL_PROJECT_API_KEY,
        "Cookie": "_csrf_token=authenticated; mp-session=pO59-bw1vxlh_wBq_hatmA|1733518522|mpRvqbXER0vtDcj3TqJ-RVhq5Wc",
    }

    try:
        response = requests.get(MATERIAL_PROJECT_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['data']
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None