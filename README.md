# 📦 Python Monorepo

Welcome to the project! This repository uses a monorepo structure to manage multiple services and shared libraries in one place.

## 🏗 Project Structure

```
├── libs/
│   └── prompt-chain/       # Shared LLM prompt chaining library
├── projects/
│   ├── analyzer/            # Analyzer application
│   └── synthesizer/         # Synthesizer application
└── pyproject.toml           # Global config (Ruff, mypy)
```

### Shared Libraries (`libs/`)

| Library | Description |
|---------|-------------|
| [`prompt-chain`](libs/prompt-chain/) | LLM prompt chaining — send prompts to OpenAI-compatible APIs and compose multi-step pipelines |

### Projects (`projects/`)

| Project | Description |
|---------|-------------|
| [`analyzer`](projects/analyzer/) | Analyzer application |
| [`synthesizer`](projects/synthesizer/) | Synthesizer application |

---

## 🚀 Getting Started (Contributor Setup)

Follow these steps to set up your local development environment.

### 1. Global Tooling Setup
We use a root virtual environment to manage development tools like `pre-commit` and `ruff`. This ensures code consistency across the entire repository.

```bash
# Create and activate the root venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt

# Install git hooks
pre-commit install
```

### 2. Working on a Specific Project
Each project has its own isolated dependencies. Navigate to the project folder to set it up:

```bash
cd projects/analyzer

# Create the project-specific venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

## 🔧 Development Workflow

### Linting & Formatting
We use **Ruff** for linting and formatting, and **mypy** for type checking. They run automatically on every commit via `pre-commit`.

- Check linting: `ruff check .`
- Fix linting: `ruff check . --fix`
- Format: `ruff format .`

### Adding Shared Libraries
To add a new shared library, create a new package in the `libs/` directory following the [src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/):

```bash
libs/my-library/
├── pyproject.toml
├── src/
│   └── my_library/
│       └── __init__.py
└── tests/
```

Then install it in your project:

```bash
cd projects/analyzer
pip install -e ../../libs/my-library
```