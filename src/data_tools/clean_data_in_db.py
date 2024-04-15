# This file contains the code to remove or clean the Questions and Answers in the SQlite Database
# This code uses the LLMDataModel class from the llm_training_data_model.py file
from src.data_tools.database_utils import get_all_items


# Function to clean the questions and save the cleaned questions back to the database
def clean_items(wrong_string, is_question=True):
    # Remove the "User:" in the questions
    items = get_all_items()
    count = 0
    if is_question:
        for item in items:
            question = item.question
            # print(f"Original Question: {question}")
            # Check if the question contains the wrong string
            if wrong_string in question:
                # Split the question by the first colon
                question = question.split(wrong_string, 1)[1].strip()
                item.question = question
                # print(f"Cleaned Question: {question}")
                count += 1
        return items, count
    else:
        for item in items:
            answer = item.answer
            # print(f"Original Answer: {answer}")
            # Check if the answer contains the wrong string
            if wrong_string in answer:
                # Split the answer by the first colon
                answer = answer.split(wrong_string, 1)[1].strip()
                item.answer = answer
                # print(f"Cleaned Answer: {answer}")
                count += 1
        return items, count
