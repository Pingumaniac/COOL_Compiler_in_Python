# COOL Lexer

## About main.py

This file contains the code for implementing a lexer in Python. Key things to note include:
1. The lexer is built using the Python PLY (Python Lex-Yacc) library, which allows us to define token patterns using regular expressions.
2. We defined token types and reserved keywords as constants (TOKENS and RESERVED) in the lexer class to make the design modular and easy to update.
3. We use PLY's @TOKEN decorator to define token patterns for various Cool language features, including integers, strings, identifiers, types, and boolean values.
4. The lexer also handles whitespace and single-line comments (--) through t_ignore.
5. Error handling is implemented in the t_error method, which prints an error message and exits the program when an illegal character is encountered.
6. Additional error handling for unclosed string and unclosed multi-line comments.
7. The lexer ensures that integers are properly parsed and stored in token values using the t_INTEGER method.
8. Reserved keywords are identified first (case-insensitive), before falling back to general identifiers (handled by the t_ID and t_TYPE methods).
9. For boolean values, the t_BOOLEAN method sets True or False depending on the matched string.
10. Line numbers are tracked using the t_newline method to ensure accurate error reporting and token positioning.
11. comment_lcount is used to keep track of the number of unresolved left multi-line comment opening "(*" along with states = (('comment', 'exclusive')) to keep track of if the content is part of a multi-line comment.
12. The lexer uses the optimize=True flag during the build phase, which improves performance by optimizing the tokenization process.
13. A debug mode is available by passing debug=True during the lexer build, providing detailed information about the lexing process.
14. We used a function that process strings in a token by token basic to correctly handle escape sequences.
15. For multi-line comments, we used two states and a counter to keep track of when we are in comments.

## About Test Cases

### good.cl

#### This file contains a valid Cool program that demonstrates a variety of Cool features. We combined a few additional variable declarations in main and foo() with the rosetta.pl from PA1 to show that the lexer can handle semi-complex COOL code. Edits to rosetta.cl include:
1. Integer addition
2. String assignment
3. Method definition (foo) that handles conditional statements (if-else)
4. A main method with a while loop and let expression to show the usage of basic control flow.
5. Proper use of out_int and out_string for output.
6. Valid string literals with escape sequences.

### bad.cl

#### This file contains multiple deliberate errors to test the lexer's error detection and other syntax errors to make sure that the lexer does not handle them. These include:
1. Unclosed multi-line comment.
2. illegal character ">".
3. Unclosed string (without second "): "Vanderbilt.
4. Invalid string literals with escape sequences.

#### Other syntax error include: (don't want the lexer to complain about them)
1. Type mismatches (attempting to add an integer and a string).
2. Method parameter type mismatch (a method expecting an integer receives a string).
3. Invalid assignment in a let expression (assigning a string to an integer).
4. An invalid method call passing incorrect types.
5. Incorrect single line comment with -.
6. Missing or extra semicolon.

How to run the program with test cases?

Type the following in the terminal/shell:

```
python3 main.py good.cl
```

```
python3 main.py bad.cl
```
