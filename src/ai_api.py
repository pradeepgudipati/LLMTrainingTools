# Function to call the OpenAI SDK to generate text based on the prompt
import os

import openai
from dotenv import load_dotenv

prompt = (
    "Given the following text, generate a list of potential FAQ questions and answers in CSV with "
    "'Question' and 'Answer' columns. Ensure that each question is specific and contains enough context "
    "to be understood independently. Return only the CSV: ")

load_dotenv('.env.local')


def call_openai_sdk(text):
    """
    Call the OpenAI SDK to generate text based on the prompt and return the completion
    The openai host and port are loaded from the .env file
    :param prompt: the prompt
    :return: the completion
    """
    global prompt
    llm_ai_host = os.environ.get("LLM_HOST")
    llm_ai_port = os.environ.get("LLM_PORT")
    llm_ai_model_llama2 = os.environ.get("LLM_MODEL_LLAMA2")
    llm_ai_model_llama3 = os.environ.get("LLM_MODEL_LLAMA3")

    client = openai.Client(api_key="fake-api-key",
                           base_url=f"{llm_ai_host}:{llm_ai_port}/v1")

    completion = client.completions.create(
        model=llm_ai_model_llama2,
        prompt=prompt + text,
        max_tokens=100000
    )
    result = completion.choices[0].text
    print(f"Result ---{result}")
    return result


def parse_openai_response(response):
    """
    Parse the response from the OpenAI SDK to extract the questions and answers
    :param response: the response from the OpenAI SDK
    :return: the questions and answers
    """
    lines = response.split("\n")
    questions = []
    answers = []
    for line in lines:
        if line.startswith("Q:"):
            questions.append(line[2:])
        elif line.startswith("A:"):
            answers.append(line[2:])
    return questions, answers
