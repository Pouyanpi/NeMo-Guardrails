# Contributing to CoLLM

Thank you for your interest in contributing to CoLLM! This document will help you get started with setting up your development environment and provide some guidelines for contributing.

## Setting Up the Development Environment

1. Ensure you have Python 3.x installed on your system. You can check your Python version by running:

```
python --version
```

2. Create a virtual environment to isolate your project's dependencies:

```
python -m venv collm_venv
```

Replace `collm_venv` with the desired name for your virtual environment directory.

3. Activate the virtual environment:

- On Windows:

  ```
  collm_venv\Scripts\activate
  ```

- On macOS and Linux:

  ```
  source collm_venv/bin/activate
  ```

4. Clone the project repository:

```
git clone https://gitlab-master.nvidia.com/dialogue-research/collm.git
```

5. Navigate to the project directory:

```
cd collm
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

## Coding Style

We follow the Black coding style for this project.

## Submitting Your Changes

Once you have made your changes and ensured they follow the coding style, you can submit a merge request on GitLab. Please provide a clear and concise description of the changes you've made, and reference any related issues or discussions.

Thank you for contributing to CoLLM!
