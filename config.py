import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MATERIAL_PROJECT_API_KEY = os.getenv("MATERIAL_PROJECT_API_KEY")
MATERIAL_PROJECT_URL = "https://api.materialsproject.org/materials/summary?_all_fields=true&_limit=1000"

ES_URL = os.getenv("ELASTICSEARCH_URL")
ES_USERNAME = os.getenv("ELASTICSEARCH_USERNAME")
ES_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ES_INDEX_NAME = "chatbot_data"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"