About Cool Semantic Analyser implementation

This project implements a semantic analyzer for the Cool programming
language.  The analyzer performs several tasks, including type checking,
class hierarchy validation, and method signature checking. The output
consists of a class map, implementation map, parent map, and an annotated
abstract syntax tree (AST). If any errors are encountered, the program
reports them with detailed error messages, following the Cool
specification for error reporting.

Design Decisions
Modular Structure: The implementation is organized into several Python
files to ensure clarity and modularity:

1. ast_nodes.py: Defines the classes and structures used to represent the
nodes in the AST.

2. ast_reader.py: Handles deserialization of the AST from the .cl-ast input
file format into Python objects.

3. class_table.py: Manages the class table, which stores information about
classes, their attributes, and methods.

4. symbol_table.py: Implements a symbol table for tracking variable and
attribute declarations within different scopes during type checking.

5. type_checker.py: Performs the core type checking and semantic analysis
tasks, ensuring conformance with the Cool type system.

6. formatter.py: Handles the serialization of the class map, implementation
map, parent map, and annotated AST into the .cl-type output format.

7. main.py: Orchestrates the process by reading the input, running the type
checker, and producing the required outputs.

Type Checking:
The type checker ensures that expressions in the program conform to the
Cool type system. Each node in the AST is annotated with its type after
being checked.
The type checker validates the types of arithmetic operations, method
calls, conditionals, and other expressions. It also checks for
redeclarations of variables and ensures method signatures match across
inheritance chains.
In the case of errors, the program outputs detailed error messages
following the required format and terminates.

Class and Method Handling:
The class table stores class definitions, attributes, and methods for each
class in the Cool program. It ensures that classes are correctly defined
and checks for cycles in the class hierarchy.
Methods are checked for proper overriding (e.g., matching signatures)
when inherited from parent classes. This is particularly handled in
the class_table.py file.

Error Handling:
Errors are detected at multiple stages, such as class redeclarations,
incorrect inheritance, or invalid type assignments in expressions.
Error messages follow the format:
ERROR: line_number: Type-Check: message,
ensuring clarity about the nature and location of the issue.

Serialization:
The class map, implementation map, parent map, and annotated AST are
serialized following the specific format described in the assignment.
This ensures compatibility with the Cool reference compiler for further
stages of the project.

Test Cases
We have provided test cases to validate the functionality of our
implementation:
1. good.cl: This is a valid Cool program that should pass semantic analysis
without any errors.
2. bad1.cl: All bad.cl are Cool programs that contain issues that should fail at the 
type-checking stage but pass for the lexer and parser (this one has class inheritance issue).
3. bad2.cl: Incorrect body and return type
4. bad3.cl: Unallowed binary operations
5. bad4.cl: Method calls with incorrect parameter types