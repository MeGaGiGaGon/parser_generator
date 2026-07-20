# Parser Generator
A simple one file library for making parsers, inspired by rust
libraries like pom, nom, winnow, and chumsky

Is made as a single file to be easilly vendorable.

See some usage examples in the examples folder

Note: Left recursion does not work

Note: Mypy is not (well) supported, it has several issues
with both the code in `parser_generator.py`, and inferring
the types of parsers.

## Predicates

The parsers that this library generates are non-backtracking.

To accomplish this, simple predicates (sequences of the input tokens) are used.

This is really nice for debugging, as parsing can only ever go strictly deeper and consume more input.
