---
description: "Custom instructions for LLMTrainingTools - Python Flask application for managing LLM training data"
---

# LLMTrainingTools Development Guidelines

## Project Overview
LLMTrainingTools is a Python Flask web application that provides utilities for creating and managing training data for Large Language Models (LLMs). The tool enables conversion between JSONL and SQLite formats, CSV to JSONL conversion, and provides a web UI for editing training data.

## Tech Stack
- **Backend**: Python 3.6+, Flask 3.0.3
- **Database**: SQLite with SQLAlchemy 2.0.29 and Flask-SQLAlchemy 3.1.1
- **Template Engine**: Jinja2 3.1.6
- **ML Libraries**: PyTorch 2.8.0, Transformers 4.53.0, scikit-learn 1.5.0
- **Vector Databases**: Milvus (pymilvus), Pinecone, Annoy
- **Additional**: NLTK, pandas, numpy, OpenAI client

## Project Structure
- `src/` - Main application source code
  - `app.py` - Flask application entry point
  - `ai_api.py` - AI/OpenAI API integrations
  - `data_tools/` - Data conversion and management utilities
  - `frontend/` - HTML templates and static files
  - `models/` - SQLAlchemy data models
- `requirements.txt` - Python dependencies
- Database path: `src/data/qa_data.db`

## Coding Standards

### Python Style
- Follow PEP 8 conventions for Python code
- Use docstrings for functions and classes (Google-style format)
- Use type hints where appropriate
- Prefer descriptive variable names (e.g., `jsonl_file_path`, `sqlite_db_path`)

### Flask Conventions
- Use Flask blueprints for modular routes when adding new features
- Keep route handlers focused and delegate business logic to separate functions
- Use Flask's `jsonify` for API responses
- Store uploaded files in `user_uploads/` subdirectories

### Database Operations
- Use SQLAlchemy ORM for all database operations
- Define models in the `models/` directory
- Use Flask-SQLAlchemy's `db` instance for session management
- Always handle database exceptions gracefully

### Data Formats
- JSONL format for training data follows OpenAI's chat completion format:
  ```json
  {
    "messages": [
      {"role": "user", "content": "question"},
      {"role": "assistant", "content": "answer"}
    ]
  }
  ```
- Database schema: `messages` table with columns `id`, `Question`, `Answer`

### File Paths
- Use `os.path.join()` for cross-platform file path construction
- Use `os.path.abspath()` for absolute paths
- Base directory: `BASE_DIR = os.path.abspath(os.path.dirname(__file__))`

### Error Handling
- Wrap file I/O and database operations in try-except blocks
- Log errors appropriately
- Return meaningful error messages in API responses
- Use Flask's error handlers for HTTP errors

## Development Practices
- Test web UI changes by running the Flask dev server (`python app.py`)
- Verify data conversions (CSV→JSONL→DB→JSONL) work end-to-end
- Check database integrity after import/export operations
- Ensure file upload size limits are respected (16 MB max)

## Security Considerations
- Never commit database files or uploaded user data
- Keep secret keys in environment variables (not hardcoded)
- Validate and sanitize all file uploads
- Use parameterized queries for all database operations

## Dependencies
- Add new dependencies to `requirements.txt`
- Pin versions for stability (use `~=` for compatible releases)
- Check compatibility with Python 3.6+ before adding new packages

## IDE Recommendations
- PyCharm (preferred) or VS Code
- Enable Flask support in IDE for better debugging
- Use virtual environments (`python -m venv`) for isolation
