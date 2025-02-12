![alt text](graphics/fosanalysis_logo.svg "FOS Analysis")
# Coding Style Guide

## Basics

Coding standards helps to create code that is readable, maintainable and accessible. The style guide based on the [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/).

PEP stands for Python Enhancement Proposal, which is a style guide document about Python coding guidelines and best practices and builds consistency within code structure and design.

This document describes the formatting, structure and design for python code in the **fosanalysis** project.

## Naming conventions

Write all new modules and package names according to the following standards to create consistency and readability:

- Use descriptive names for classes, functions, variables.
- **Package and Module Names** should have short, all-lowercase names.
- **Class Names** should use the CapitalizedWords (or CapWords, or CamelCase)
- **Function and Variable Names** should be lowercase, with words separated by underscores as necessary to improve readability.
- **Method Names and Instance Variables** uses the function naming rules and one leading underscore for non-public methods and instance variables.
- **Constants** are defined on a module level and written in all CAPITAL letters with underscores separating words.

## Indentation

- Spaces are the preferred indentation method.
- Use 4 spaces for each indentation level.
- Continuation lines should align wrapped elements either vertically inside parentheses, brackets and braces.
- When using hanging indent, there should be no arguments on the first line.

```python
# Aligned with opening delimiter. 
foo = long_function_name(var_one, var_two, 
                         var_three, var_four)

# Add 4 spaces (extra indentation) to distinguish arguments from the rest.
def long_function_name(
        var_one, var_two, var_three,
        var_four):
    print(var_one)

# Hanging indents should add a level.
foo = long_function_name(
    var_one, var_two,
    var_three, var_four) 
```

## Maximum Line Length

- Limit all lines to a maximum of 89 characters.
- Comments and docstrings should be limited to 72 characters.
- Long lines can be broken over multiple lines by wrapping expressions in parentheses.
- Backslashes where acceptable for cases where parentheses cannot be used.

```python
my_very_big_string = ("For a long time I used to go to bed early.
                      Sometimes, when I had put out my candle,
                      my eyes would close so quickly ".)

with open('/path/to/some/file/you/want/to/read') as file_1, \
     open('/path/to/some/file/being/written', 'w') as file_2:
    file_2.write(file_1.read())
```
## Blank Lines

- Surround top-level function and class definitions with two blank lines.
- Method definitions inside a class are surrounded by a single blank line.
- Use blank lines in functions, sparingly, to indicate logical sections.

## Whitespace in Expressions and Statements

- Avoid extraneous whitespace:
```python
# Inside parentheses, brackets or braces and before parenthesis
spam(ham[1], {eggs: 2})

# Immediately before a comma, semicolon or colon
if x == 4: print(x, y)
```

- Surround binary operators with a single space on either side
```python
i = i + 1
submitted += 1

# Adding whitespace around the operators with the lowest priority
x = x*2 – 1
c = (a+b) * (a-b)
```

- Function annotations should use the normal rules for colons and spaces
```python
def munge(input: str, sep: str = None, limit=1000) -> int:
```

- Multiple statements on the same line are prohibited.

## Comments

Comments are essential to build a codebase that others can understand. Doxygen is our documentation generator tool, so write your source code comments in the correct format to produce standardized output.

- Comments must be written in complete sentences.
- Comments must be up to date. For code changes, update your comments to match the current code function.
- Write code comments in English.
- Use # and a single space as start for a block comment.
- Inline comments should be used sparingly.
- Conventions for good documentation strings are defined at the [Doxygen](https://www.doxygen.nl/manual/docblocks.html) page.
- Define the correct documentation for doxygen (use `r"""` for opened documentation to prevent warnings)
 ```python
r"""\package module_name
Documentation for this module.
More details.
"""

def func(x: float):
    r"""
    Documentation for a function.
    \param x Value for x.
    \return Square of x value.
    """
    return x * x

class PyClass:
    r"""
    Documentation for a class.
    """
    def __init__(self):
        r""" The constructor. """
        self._memVar = 0;
```

## Imports

- Imports should usually be on separate lines.
- Imports always put at the top of the file, just after any module comments and docstrings and before module globals and constants.
- Imports should be grouped in the following order, separated with a blank line:
    1. Standard library imports.
    2. Related third party imports.
    3. Local application/library specific imports.
- Multiple imports from one package can be written in one line.
- Absolute paths are recommended.
```python
from myclass import MyClass, SpecialClass
from foo.bar.yourclass import YourClass
```
