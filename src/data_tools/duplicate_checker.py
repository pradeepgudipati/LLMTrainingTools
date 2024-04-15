from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
            ques = item.user
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
            answers = item.assistant
            answers.append(answers.lower())
            count += 1
        return answers


# Vectorize the questions using TfidfVectorizer
def vectorize_items(items):
    # Initialize a TfidfVectorizer
    vectorizer = TfidfVectorizer()
    # print the top 10 questions
    print(items[:10])
    # Vectorize the questions
    items_vectors = vectorizer.fit_transform(items)
    # Now, question_vectors is a matrix where each row represents a different question
    # You can use this matrix to find similar questions, identify duplicates, etc.
    return items_vectors


# Function to find similar items using dot product
def find_similar_items(items_vectors, item_index, top_n=5):
    # Calculate the dot product of the question with all other questions
    items_dot_products = items_vectors.dot(items_vectors[item_index].T)
    # Convert the sparse matrix to a dense one
    items_dot_products_dense = items_dot_products.toarray()
    # Get the indices of the questions with the highest dot products
    similar_items_indices = items_dot_products_dense.argsort(axis=0)[-top_n:][::-1]
    return similar_items_indices


# Function to find similar items using cosine similarity
def find_similar_items_cosine(items_vectors, item_index, top_n=5):
    # Calculate the cosine similarity of the question with all other questions
    items_similarities = cosine_similarity(items_vectors, items_vectors[item_index].reshape(1, -1))
    # Get the indices of the questions with the highest similarities
    similar_item_indices = items_similarities.argsort(axis=0)[-top_n:][::-1]
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
            # If similarity is above a certain threshold, consider the items as duplicates
            if similarity[0][0] > 0.9:  # You can adjust this threshold as needed
                duplicate_pairs.append((db_items[i], db_items[j]))

    return duplicate_pairs
