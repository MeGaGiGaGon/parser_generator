# Parser Generator
A simple one file library for making parsers, inspired by rust
libraries like pom, nom, winnow, and chumsky

`parser.py` is for simple parsers that don't need span information.

`spanned_parser.py` works the almost the same, with additional tools
for tracking consumed spans.

Is made as a single file to be easilly vendorable.

# Examples

These examples use full type hints for clarity.

Most type checkers will be able to infer the types of
these parsers without them, so they will usually only
be needed for more complex/erroring cases.

# Repetitions
rule `A B+ C`

rule_rest = choose(
    B.then(rule_rest).map(lambda x: ([x[0], *x[1][0]], x[1][1])),
    C.map(lambda x: ([], x))
)
rule = A.then(rule_rest)

# Contributing

