# Cool Semantic Analyzer

## Overview

This project implements a semantic analyzer for the Cool programming language. The analyzer performs several essential tasks, including:

- **Type Checking**
- **Class Hierarchy Validation**
- **Method Signature Checking**

The output consists of a class map, implementation map, parent map, and an annotated abstract syntax tree (AST). If any errors are encountered, they are reported with detailed messages following the Cool specification for error reporting.

## Design Decisions

### Modular Structure
The implementation is divided into several Python files for clarity and modularity:

- **`ast_nodes.py`:** Defines the classes and structures used to represent the nodes in the AST.
- **`ast_reader.py`:** Handles deserialization of the AST from the `.cl-ast` input file format into Python objects.
- **`class_table.py`:** Manages the class table, which stores information about classes, their attributes, and methods.
- **`symbol_table.py`:** Implements a symbol table to track variable and attribute declarations within different scopes during type checking.
- **`type_checker.py`:** Performs core type checking and semantic analysis tasks, ensuring conformance with the Cool type system.
- **`formatter.py`:** Serializes the class map, implementation map, parent map, and annotated AST into the `.cl-type` output format.
- **`main.py`:** Orchestrates the overall process by reading inputs, running the type checker, and producing the required outputs.

## Key Features

### Type Checking
The type checker ensures that expressions conform to the Cool type system. After checking, each node in the AST is annotated with its type. Key validations include:

- Type checking of arithmetic operations, method calls, conditionals, and other expressions.
- Redeclaration detection of variables.
- Verification of method signatures across inheritance chains.

In the event of errors, the program outputs detailed error messages and terminates.

### Class and Method Handling
- The class table maintains class definitions, attributes, and methods for each class in the Cool program.
- It ensures that classes are correctly defined and checks for cycles in the class hierarchy.
- Methods inherited from parent classes are checked for proper overriding, including signature matching.

This logic is handled primarily in `class_table.py`.

### Error Handling
Errors are detected at multiple stages, including:

- Class redeclarations.
- Incorrect inheritance.
- Invalid type assignments in expressions.

Error messages follow the format:

ERROR: line_number: Type-Check: message

This ensures clarity regarding the nature and location of the issue.

### Serialization
The class map, implementation map, parent map, and annotated AST are serialized following the assignment's specific format. This ensures compatibility with the Cool reference compiler for further project stages.

## Test Cases

The following test cases have been provided to validate the semantic analyzer:

1. **`good.cl`:** A valid Cool program that should pass semantic analysis without errors.
2. **`bad1.cl`:** Contains a class inheritance issue that should fail during type-checking.
3. **`bad2.cl`:** Incorrect body and return type.
4. **`bad3.cl`:** Invalid binary operations.

This semantic analyzer offers an organized, modular approach to verifying Cool programs, ensuring conformance to the Cool language specification and robust error handling.
