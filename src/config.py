import os
from pathlib import Path

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_project_env() -> None:
    values = {}
    for filename in (".env.example", ".env"):
        path = PROJECT_ROOT / filename
        if path.exists():
            values.update(
                {
                    key: value
                    for key, value in dotenv_values(path).items()
                    if value is not None
                }
            )

    for key, value in values.items():
        os.environ.setdefault(key, value)


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} must be set in the environment or .env.example")
    return value
