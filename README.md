# LLMTrainingTools

A local data workbench for preparing chat fine-tuning datasets from CSV, SQLite, and JSONL.

LLMTrainingTools runs locally as a Flask app. It helps you import CSV/JSONL data, edit examples in a table, validate common dataset issues, back up the SQLite database, and export clean JSONL.

![LLMTrainingTools table editor](screenshot.png)

## Features

- Local Flask editor for CSV, SQLite, and JSONL training data.
- Core install stays lightweight: Flask, SQLite, SQLAlchemy, and dotenv only.
- Optional AI/vector dependencies live behind the `ai` extra.
- JSONL validation for OpenAI/HF-style chat records, roles, empty answers, duplicated questions, overlong examples, PII/secrets, encoding issues, and CSV headers.
- Dataset shapes beyond Question/Answer: chat messages, preference pairs, tool traces, RAG chunks with metadata, and eval records with expected answers or rubrics.
- SQLite backup/restore, JSONL import/export, and CSV to JSONL conversion.

## Requirements

- Python 3.10 to 3.13
- [uv](https://docs.astral.sh/uv/)

## Quickstart

```bash
git clone https://github.com/pradeepgudipati/LLMTrainingTools.git
cd LLMTrainingTools
cp .env.example .env.local
uv sync
uv run python -m src.app
```

Open http://127.0.0.1:5000.

You can also use the packaged CLI:

```bash
uv run llm-training-tools
```

## Dependency Groups

Core app:

```bash
uv sync
```

AI/vector features:

```bash
uv sync --extra ai
```

Development checks:

```bash
uv sync --dev
./precommit.sh
uv run pytest
```

Dependencies are declared in `pyproject.toml`. The `requirements.txt` file is only a compatibility note for users looking for the old pip workflow.

## 60-Second Walkthrough

1. Start the app with `uv run python -m src.app`.
2. Open http://127.0.0.1:5000.
3. Use the CSV to JSONL action with `samples/sample_qa.csv`.
4. Import the generated JSONL into SQLite.
5. Edit any row in the table.
6. Run validation before export.
7. Export JSONL for fine-tuning or evaluation.

Sample CSV:

```csv
Question,Answer
What is JSONL?,JSONL stores one JSON object per line.
When should I use a system message?,Use it to set durable behavior or context for the assistant.
```

Exported chat JSONL:

```json
{"messages":[{"role":"user","content":"What is JSONL?"},{"role":"assistant","content":"JSONL stores one JSON object per line."}]}
```

Additional examples are in `samples/sample_chat.jsonl`.

## Supported Dataset Shapes

Chat messages:

```json
{"messages":[{"role":"system","content":"Answer briefly."},{"role":"user","content":"What is JSONL?"},{"role":"assistant","content":"One JSON object per line."}]}
```

Preference pairs:

```json
{"prompt":"Pick the clearer answer.","chosen":"Use validation before export.","rejected":"Try uploading it."}
```

RAG chunks:

```json
{"text":"Fine-tuning examples should be specific and consistent.","metadata":{"source":"guide","chunk_id":"001"}}
```

Eval records:

```json
{"question":"Is the answer correct?","expected_answer":"Yes","rubric":"Must directly answer the question."}
```

## Configuration

Copy `.env.example` to `.env.local` for local settings. Do not commit `.env.local`.

Important settings:

```bash
FLASK_SECRET_KEY=change-me-before-sharing
FLASK_RUN_HOST=127.0.0.1
FLASK_RUN_PORT=5000
LLMTOOLS_DB_PATH=src/data/qa_data.db
```

AI features require optional dependencies and API keys:

```bash
uv sync --extra ai
OPENAI_API_KEY=...
```

## Docker Compose

```bash
docker compose up --build
```

Open http://127.0.0.1:5000.

## CI

GitHub Actions installs dependencies with uv, runs `./precommit.sh`, and runs pytest on Python 3.10, 3.11, and 3.12.

## License

MIT. See `LICENSE`.
