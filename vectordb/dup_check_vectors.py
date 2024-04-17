# Description: This script is used to check for duplicate items in the database.
# It uses the TfidfVectorizer to vectorize the text items and pushes them to pinecone
# for similarity check. The script is used to check for duplicate items in the database


from dotenv import load_dotenv

load_dotenv("vectordb.env")



