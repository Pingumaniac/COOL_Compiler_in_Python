# x86 Code Generator from COOL

## Overview

This compiler takes a Cool Annotated Abstract Syntax Tree (AAST) from a
`.cl-type` file and generates corresponding **x86-64** assembly code.
The generated assembly adheres to the System V AMD64 ABI and is compatible
with Linux environments.

## Design Decisions

1. **Modular Structure**: The compiler is divided into multiple modules
to enhance readability and maintainability:
   - **`main.py`**: Entry point.
   - **`ast_parser.py`**: Parses the `.cl-type` file.
   - **`class_table.py`**: Manages class symbols and inheritance.
   - **`symbol_table.py`**: Manages symbol tables during code generation.
   - **`code_generator.py`**: Core component that translates AST to assembly.
   - **`helpers.py`**: Utility functions for label generation and string caching.
   - **`errors.py`**: Handles runtime error reporting.

2. **x86-64 Assembly Generation**: The compiler targets **x86-64**
assembly, leveraging standard conventions and optimizing for performance.

3. **VTables for Method Dispatch**: Implements virtual tables for dynamic
method dispatch, supporting inheritance and method overriding.

4. **Runtime Error Handling**: Generates assembly code to handle runtime
errors gracefully, printing error messages and exiting appropriately.

5. **Object Layout**: Each Object follow the object layout of id, size, vtable,
and then one field for each attribute. String Obejcts have an additional field
for length, which support String.length().


## Test Cases

Five test cases are provided to evaluate the compiler's correctness and
robustness:

1. **`test1.cl`**: This is a valid Cool program that should pass semantic analysis
without any errors.

Made this code from our PA1.

2. **`test2.cl`**: This code is used to test the while loop functionality
of COOL.

The loop executes 10 times because counter starts at 0 and increments by
1 in each iteration. After the loop terminates, the result of the while
loop (Object) is determined. The type_name() method on this result
returns the string "Object". This string is passed to out_string, which
prints "Object" to the output.


3. **`test3.cl`**: This code is an implementation of a Cellular Automaton
in COOL, a simple programming language often used in academic settings to
teach object-oriented programming. Cellular Automata are systems where
cells exist on a grid and change states over discrete time steps based
on predefined rules that consider the states of neighboring cells.

This demonstrates concepts such as:

- Object-oriented design.
- Simulation of discrete-time systems.
- Handling edge cases in grid-based computations (e.g., wrapping neighbors).

4. **`test4.cl`**: This test code demonstrates inheritance, polymorphism,
and type identification in COOL. The goal is to show how objects of
different classes interact and how their types are resolved dynamically
during runtime.

This demonstrates concepts such as:

- The type of each created object.
- How polymorphism retains the actual type of an object (SubClass remains
SubClass even when referenced as RootClass).
- The type of self when called on a SubClass instance.

5. **`test5.cl`**: This test code demonstrates the use of the abort
method in COOL, showcasing how program execution can be terminated
abruptly.

Each test case covers different aspects of the language and ensures that
the compiler handles both typical and edge-case scenarios effectively.
