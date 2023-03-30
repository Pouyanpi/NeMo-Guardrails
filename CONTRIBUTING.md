# Contributing to Colang Flows

Thank you for your interest in contributing to Colang Flows! This document will help you get started with setting up your development environment and provide some guidelines for contributing.

## Setting Up the Development Environment

1. Ensure you have Python 3.x installed on your system. You can check your Python version by running:

```
python --version
```

2. Create a virtual environment to isolate your project's dependencies:

```
python -m venv colang_venv
```

Replace `colang_venv` with the desired name for your virtual environment directory.

3. Activate the virtual environment:

- On Windows:

  ```
  colangflows_venv\Scripts\activate
  ```

- On macOS and Linux:

  ```
  source colangflows_venv/bin/activate
  ```

4. Clone the project repository:

```
git clone https://gitlab-master.nvidia.com/dialogue-research/colangflows.git
```

5. Navigate to the project directory:

```
cd colangflows
```

6. Install the development dependencies from `requirements-dev.txt`:

```
pip install -r requirements-dev.txt
```

This will install pre-commit, pylint, mypy, and any other development tools specified in the `requirements-dev.txt` file.

7. Set up pre-commit hooks:

```
pre-commit install
```

This will ensure that the pre-commit checks, including Black, pylint, and mypy, are run before each commit.

## Folder Structure

The project is structured as follows:
- `colangflows/actions/`: implementation of various actions.
- `colangflows/cli/`: implementation of the Colang Flows CLI.
- `colangflows/flows/`: implementation of the Colang Flows runtime.
- `colangflows/language/`: Colang language parser.
- `colangflows/llm`: various utilities for working with LLMs.
- `colangflows/rails/`: implementation of various rails systems.
- `colangflows/rails/llm`: rails for LLMs.

## Coding Style

We follow the Black coding style for this project.

## Submitting Your Changes

Once you have made your changes and ensured they follow the coding style, you can submit a merge request on GitLab. Please provide a clear and concise description of the changes you've made, and reference any related issues or discussions.

Thank you for contributing to Colang Flows!
