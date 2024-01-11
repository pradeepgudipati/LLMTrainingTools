# LLMTrainingTools
Some simple tools to help build the Training Data for LLM Chatbot Training. 


# JSONL Editor

This folder contains the code to do the following

1. Convert the JSONL file to a SQL Lite Db and vice versa
2. Flask UI application to edit the training data.

## Pre-requisites

Python 3.6 or above
Pip
Visual Studio Code or any other IDE - Pycharm(preferred)
SQL Lite

## What does this Repo Do

### 1. JSONL to DB - [jsonl_data_to_db](jsonl_data_to_db)

This [jsonl_to_sqllite.py](jsonl_data_to_db%2Fjsonl_to_sqllite.py) python file converts the jsonl data to a sqllite
database with a table called messages. This table has 3 rows

1. id - Primary key
2. User - Contains the Question
3. Assistant - Contains the answer to the Question

### 2. DB to JSONL : [db_to_jsonl.py](jsonl_data_to_db%2Fdb_to_jsonl.py)

The following Python file converts the sqllite database to a jsonl file
The format of the jsonl is as follows

```json
{
  "messages": [
    {
      "role": "user",
      "content": ""
    },
    {
      "role": "assistant",
      "content": ""
    }
  ]
}
...
```

### 3. Flask Application for editing the training data

- Flask Server App - [app.py](app.py)
- Flask HTML Template - [table_view.html](templates%2Ftable_view.html)
- Data Model [llm_training_data_model.py](models%2Fllm_training_data_model.py)

### 4. Training files

1. JSONL File - [qa_data.jsonl](jsonl_data_to_db%2Fdata%2Fqa_data.jsonl)
2. SQL Lite DB file - [qa_data.db](jsonl_data_to_db%2Fdata%2Fqa_data.db)