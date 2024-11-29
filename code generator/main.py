# main.py

import sys
from ast_parser import ASTParser
from symbol_table import SymbolTable
from code_generator import CodeGenerator

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <file.cl-type>")
        sys.exit(1)

    filename = sys.argv[1]

    # Parse the AAST
    parser = ASTParser(filename)
    ctab, ast = parser.parse()

    # Initialize symbol table
    stab = SymbolTable()

    # print()

    # Initialize code generator
    generator = CodeGenerator(ctab, ast, stab, filename)
    generator.generate()

    print("Assembly generation completed successfully.")

if __name__ == "__main__":
    main()
