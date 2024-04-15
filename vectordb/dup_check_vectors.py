# Description: This script is used to check for duplicate items in the database.
# It uses the TfidfVectorizer to vectorize the text items and pushes them to pinecone
# for similarity check. The script is used to check for duplicate items in the database


import os

from dotenv import load_dotenv

from src.data_tools.database_utils import get_all_items
from src.data_tools.duplicate_checker import preprocess_text_items, vectorize_items
from src.models.llm_training_data_model import LLMDataModel

load_dotenv("vectordb.env")



