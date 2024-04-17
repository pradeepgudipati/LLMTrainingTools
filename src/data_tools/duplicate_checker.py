import datetime

import pandas as pd
from annoy import AnnoyIndex
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

from src.data_tools.database_utils import get_all_items
from src.models.llm_training_data_model import LLMDataModel


# Function to preprocess the text - convert all questions or answers to lower
def preprocess_text_items(items, is_question=True):
    questions = []
    answers = []
    count = 0
    if is_question:
        for item in items:
            # Append the question to the questions list after removing any leading or trailing whitespaces and
            #  removing - Category: * ; Question: from the question = * means any character string
            ques = item.question
            if ":" in ques:
                ques = ques.rsplit(":", 1)[1].strip()
                questions.append(ques.lower())
            else:
                questions.append(ques.lower())
            count += 1
        return questions
    else:
        for item in items:
            # Append the answer to the answers list after removing any leading or trailing whitespaces
            answers.append(item.answer.lower())
            count += 1
        print("Preprocessed Total Answers -- ", count)
        return answers


# Vectorize the questions using TfidfVectorizer
def vectorize_items(items):
    # Initialize a TfidfVectorizer
    vectorizer = TfidfVectorizer()
    # Vectorize the questions
    items_vectors = vectorizer.fit_transform(items)
    # Now, items_vectors is a matrix where each row represents a different item
    # You can use this matrix to find similar items or identify duplicates, etc.
    return items_vectors


# Function to find similar items using dot product
def find_similar_items(items_vectors, item_index, top_n=5):
    # Calculate the dot product of the question with all other questions
    items_dot_products = items_vectors.dot(items_vectors[item_index].T)
    # Convert the sparse matrix to a dense one
    items_dot_products_dense = items_dot_products.toarray()
    # Get the indices of the questions with the highest dot products
    similar_items_indices = items_dot_products_dense.argsort(axis=0)[-top_n:][::-1]
    print(similar_items_indices)
    return similar_items_indices


# Function to find similar items using cosine similarity
def find_similar_items_cosine(items_vectors, item_index, top_n=5):
    # Calculate the cosine similarity of the question with all other questions
    items_similarities = cosine_similarity(items_vectors, items_vectors[item_index].reshape(1, -1))
    # Get the indices of the questions with the highest similarities
    similar_item_indices = items_similarities.argsort(axis=0)[-top_n:][::-1]
    print("Similar items are -- ", similar_item_indices)
    return similar_item_indices


# Function to check for duplicates in answers in the database
def find_duplicate_answers():
    # Get all items from the database
    items = get_all_items()
    # Preprocess the text
    answers = preprocess_text_items(items)
    # Vectorize the answers
    answer_vectors = vectorize_items(answers)
    # Find similar answers to the first answer
    similar_answer_indices = find_similar_items_cosine(answer_vectors, 0)
    print("Similar answers are -- ", similar_answer_indices)
    # Print the number and text of duplicate answers
    for i, index in enumerate(similar_answer_indices):
        print(f"Duplicate {i + 1}: {answers[index[0]]}")


# Execute the above functions now.
def check_duplicates(is_question):
    # Get all items from the database
    db_items = get_all_items(LLMDataModel)
    # Preprocess the text
    items_text = preprocess_text_items(db_items, is_question)
    # Vectorize the questions
    items_vectors = vectorize_items(items_text)

    duplicate_pairs = []

    # Compare each item to every other item
    for i in range(len(db_items)):
        for j in range(i + 1, len(db_items)):
            # Calculate similarity between item i and item j
            similarity = cosine_similarity(items_vectors[i].reshape(1, -1), items_vectors[j].reshape(1, -1))
            print(f"Similarity between {db_items[i]} and {db_items[j]}: {similarity[0][0]}")
            # If similarity is above a certain threshold, consider the items as duplicates
            if similarity[0][0] > 0.9:  # You can adjust this threshold as needed
                print(f"Duplicate Pair: {db_items[i]} and {db_items[j]}")
                duplicate_pairs.append((db_items[i], db_items[j]))
    print("Duplicate Pairs are --", len(duplicate_pairs))
    return duplicate_pairs


def duplicate_checker_vectors(is_question):
    db_items = get_all_items(LLMDataModel)
    # Preprocess the text
    items_text = preprocess_text_items(db_items, is_question)

    # Convert your strings into vectors
    X = vectorize_items(items_text)

    # Build Annoy index
    f = X.shape[1]  # Length of item vector that will be indexed
    t = AnnoyIndex(f, 'angular')  # Length of item vector that will be indexed and 'angular' for cosine distance
    for i in range(X.shape[0]):
        v = X[i].toarray()[0]
        t.add_item(i, v)

    t.build(10)  # 10 trees
    t.save('test.ann')

    # Load Annoy index
    u = AnnoyIndex(f, 'angular')
    u.load('test.ann')  # super fast, will just mmap the file

    # Find duplicates
    duplicates = []
    for i in tqdm(range(X.shape[0]), desc="Checking for duplicates"):
        v = X[i].toarray()[0]
        nearest = u.get_nns_by_vector(v, 2)  # find the 2 nearest neighbors
        if nearest[0] == i:  # if the nearest neighbor is itself
            similarity = cosine_similarity(X[i].reshape(1, -1), X[nearest[1]].reshape(1, -1))
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
