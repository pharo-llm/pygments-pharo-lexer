# pygments-pharo-lexer

A standalone Pygments plugin package for the Pharo Smalltalk lexer.

## Installation

```console
pip install pygments-pharo-lexer==0.1.0
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
