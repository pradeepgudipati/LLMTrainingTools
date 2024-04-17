import datetime
import string

import nltk
import pandas as pd
from annoy import AnnoyIndex
from data_tools.database_utils import get_all_items
from models.llm_training_data_model import LLMDataModel
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

# Download the stopwords from NLTK
nltk.download('stopwords')
nltk.download('wordnet')

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()


def preprocess_text_items(items, is_question=True):
    processed_items = []
    for item in items:
        text = item.question if is_question else item.answer
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Tokenize the text
        words = nltk.word_tokenize(text)
        # Remove stopwords and lemmatize the words
        words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
        processed_items.append(' '.join(words))
    return processed_items


# Vectorize the questions using TfidfVectorizer
def vectorize_items(items):
    # Initialize a TfidfVectorizer
    vectorizer = TfidfVectorizer()
    # Vectorize the questions
    items_vectors = vectorizer.fit_transform(items)
    # Now, items_vectors is a matrix where each row represents a different item
    # You can use this matrix to find similar items or identify duplicates, etc.
    return items_vectors


# Check for duplicates in questions or answers and store them in a csv file. The function takes a boolean parameter
def duplicate_checker_vectors(is_question):
    # Get all items from the database
    db_items = get_all_items(LLMDataModel)
    # Preprocess the text
    items_text = preprocess_text_items(db_items, is_question)

    # Convert your strings into vectors
    vectors = vectorize_items(items_text)

    # Build Annoy index
    f = vectors.shape[1]  # Length of item vector that will be indexed
    t = AnnoyIndex(f, 'angular')  # Length of item vector that will be indexed and 'angular' for cosine distance
    for i in range(vectors.shape[0]):
        v = vectors[i].toarray()[0]
        t.add_item(i, v)

    t.build(10)  # 10 trees
    t.save('test.ann')

    # Load Annoy index
    u = AnnoyIndex(f, 'angular')
    u.load('test.ann')  # super fast, will just mmap the file

    # Find duplicates
    duplicates = []
    for i in tqdm(range(vectors.shape[0]), desc="Checking for duplicates"):
        v = vectors[i].toarray()[0]
        nearest = u.get_nns_by_vector(v, 2)  # find the 2 nearest neighbors
        if nearest[0] == i:  # if the nearest neighbor is itself
            similarity = cosine_similarity(vectors[i].reshape(1, -1), vectors[nearest[1]].reshape(1, -1))
            if similarity[0][0] > 0.95:  # Adjust this threshold as needed
                duplicates.append((db_items[i].id, db_items[i].question, db_items[i].answer, db_items[nearest[1]].id,
                                   db_items[nearest[1]].question, db_items[nearest[1]].answer))
    print("Duplicates are -- ", len(duplicates))
    # Create a DataFrame from the duplicates list
    df = pd.DataFrame(duplicates, columns=['id 1', 'Question 1', 'Answer 1', 'Id 2', 'Question 2 ', 'Answer 2'])

    file_name = 'duplicates' + datetime.datetime.now().strftime("%d_%b_%y_t%H_%M") + '.csv'
    # Export the DataFrame to a CSV file
    df.to_csv(file_name, index=False)
    return duplicates
