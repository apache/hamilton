# Parallelizable Subclass

## Overview

When annotating a function with `Parallelizable`, it is not possible to specify in the annotation what the type returned by the function will actually be, and these are not identified by a linter or other tools as static type checking. Especially for functions that can be used with or without Hamilton, this can be a problem.

To solve this problem, it is possible to create subclasses of the `Parallelizable` classes, as demonstrated in this example.

## Running

The `notebook.ipynb` exemplifies how to use a `Parallelizable` subclass.
