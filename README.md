# pygments-pharo-lexer

A standalone Pygments plugin package for the Pharo Smalltalk lexer.

## Installation

```console
pip install pygments-pharo-lexer
```

## Usage

```python
from pygments.lexers import get_lexer_by_name

lexer = get_lexer_by_name("pharo")
```

You can also import the lexer class directly:

```python
from pygments_pharo.lexer import PharoLexer
```

## Releasing

Build and verify the package locally before publishing:

```console
python -m pip install -e .[dev]
python -m pytest
python -m build
python -m twine check dist/*
```

Publishing is automated by the `Publish to PyPI` GitHub Actions workflow. In
PyPI, create a pending Trusted Publisher for project `pygments-pharo-lexer` with
owner `pharo-llm`, repository `pygments-pharo-lexer`, workflow `publish.yml`,
and environment `pypi`, then push a version tag:

```console
git tag v0.1.0
git push origin v0.1.0
```
