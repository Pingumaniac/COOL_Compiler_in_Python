# main.py

import sys
from ast_nodes import *
from ast_reader import ASTReader
from class_table import ClassTable
from formatter import ASTFormatter
from symbol_table import SymbolTable
from type_checker import TypeChecker

class SemanticAnalyzer:
    def __init__(self, ast, classTable, formatter):
        self.ast = ast
        self.classTable = classTable
        self.formatter = formatter
        self.symbolTable = SymbolTable()
        self.typeChecker = TypeChecker(classTable, formatter, self.symbolTable)

    def analyze(self):
        self.typeChecker.symbolTable.defining_types(self.all_available_types())
        for cls in self.ast:
            self.typeCheckClass(cls)
            self.typeChecker.symbolTable.clearSymbolTable()


    def validateInheritance(self):
        for cls in self.classTable.allClasses():
            parent = self.classTable.getParent(cls)

            # All classes except Object must have a parent
            if parent:
                if not self.classTable.getClass(parent):
                    self.reportError("0", f"Class {cls} inherits from non-existent class {parent}")

                # Check for inheritance cycles
                visited = []
                current = parent
                while current:
                    if current in visited:
                        self.reportError("0", f"Inheritance cycle detected involving class {cls}")
                    visited.append(current)
                    current = self.classTable.getParent(current)

    def registerFeatures(self, cls):
        className = cls.name[1]
        for feature in cls.features:
            if isinstance(feature, AttributeInitFeature):
                attrName = feature.name[1]
                attrType = feature.type[1]
                initExpr = feature.init

                # Check for attribute redeclaration
                if self.classTable.findAttribute(className, attrName):
                    self.reportError(feature.name[0], f"Attribute {attrName} already declared in class {className} or its parents")

                # Add attribute to ClassTable
                self.classTable.addAttribute(className, attrName, attrType, initExpr)

            elif isinstance(feature, MethodFeature):
                methodName = feature.name[1]
                args = [(arg[0][1], arg[1][1]) for arg in feature.formals]
                returnType = feature.returnType
                body = feature.body
                if self.classTable.getMethod(className, methodName):
                    self.reportError(feature.name[0], f"Method {methodName} already declared in class {className}")
                parentMethod = self.classTable.findMethod(self.classTable.getParent(className), methodName)
                if parentMethod:
                    if parentMethod[1] != args or parentMethod[2][1] != returnType[1]:
                        self.reportError(feature.returnType[0], f"Inherited method {methodName} has incompatible signature in class {className}")
                self.classTable.addMethod(className, methodName, args, returnType, body)


    def all_available_types(self):
        types = []
        for type in self.classTable.data:
            types.append(type)
        return types

    def typeCheckAttributes(self, class_name):
        attributes = self.classTable.data[class_name]['attributes']
        for attribute in attributes:
            self.typeChecker.symbolTable.addClassSymbol(attribute[0], attribute[1])
        # print()
        # print("___________________________")
        # print(class_name)
        for attribute in attributes:
            nodetype = attribute[2]
            if nodetype != None:   
                expr_type = self.typeCheckExpr(attribute[2], class_name)
                declared_type = attribute[1]
                if not self.typeChecker.compatible(declared_type, expr_type):
                    self.reportError(attribute[2].line, f"assigning a {expr_type} into a {attribute[1]} variable")
        # print("finished checking attributes")

    def typeCheckExpr(self, expr, self_typee):
        if not isinstance(expr, ExprNode):
            self.reportError(0, "Unrecognized instance in typeCheckExpr")
        self.typeChecker.checkLetVarTypes(expr, self_typee)
        type = self.typeChecker.annotateExpr(expr, self_typee)
        return type

    def process_formal_list(self, formal_list):
        scope_vars = []
        for formal in formal_list:
            if not isinstance(formal, FormalNode):
                self.reportError(0, "strange formal node type")
            if formal.arg_type not in self.typeChecker.symbolTable.types:
                self.reportError(formal.arg_type_lino, "formal type {formal.arg_type} not declared")
            if formal.arg_name == 'self':
                self.reportError(formal.arg_type_lino, "self cannot be a formal parameter")
            if formal.arg_type == 'SELF_TYPE':
                self.reportError(formal.arg_type_lino, "SELF_TYPE cannot be a formal type")
            scope_vars.append((formal.arg_name, formal.arg_type))

        formal_set = set([formal[0] for formal in scope_vars])
        if len(formal_set) != len(scope_vars):
            self.reportError(formal.arg_type_lino, "duplicate formal paremeters")

        return scope_vars
            

    def typeCheckMethods(self, class_name):
        methods = self.classTable.data[class_name]['methods']
        
        for method in methods:
            if method[4] != "IO":
                self.typeChecker.symbolTable.clearScopeData()
                scope_vars = self.process_formal_list(method[1])
                self.typeChecker.symbolTable.enter_scope(scope_vars)
                return_type = method[2][1]

                method_body = method[3]

                if isinstance(method_body, ExprNode):
                    body_type = self.typeCheckExpr(method_body, class_name)
                    
                    if method_body.annotatedType != 'SELF_TYPE' and return_type == 'SELF_TYPE':
                        self.reportError(method[2][0], "body and return type do not conform")
                    
                    if body_type == "SELF_TYPE":
                        body_type = class_name
                else:
                    
                    body_type = method_body[1]
                    if body_type == "SELF_TYPE":
                        body_type = method[4]
            
                

                if return_type == "SELF_TYPE":
                    return_type = method[4]
                if return_type not in self.typeChecker.symbolTable.types:
                    self.reportError(method[2][0], f"return type {return_type} not declared")
                
                
                if not self.typeChecker.compatible(return_type, body_type):
                    self.reportError(0, f"body is type {body_type} while return type is {return_type}")

    def typeCheckClass(self, cls):
        className = cls.class_name
        self.typeCheckAttributes(className) 
        self.typeCheckMethods(className)


    def reportError(self, line, message):
        print(f"ERROR: {line}: Type-Check: {message}")
        sys.exit(1)

def printAST(ast):
    for c in ast:
            print(c.class_name)
            print(c.parent_type)
            for f in c.featureList:
                print(f.feature_type)
                if f.feature_type == "method":
                    print(f.method_name)
                    for arg in f.formalsList:
                        print(arg.arg_name)
                        print(arg.arg_type)
                    print(f.return_type)
                elif f.feature_type == "attribute_init":
                    print(f.attribute_name)
                    print(f.attribute_type)
                elif f.feature_type == "attribute_no_init":
                    print(f.attribute_name)
                    print(f.attribute_type)

def print_nested_dict(d, indent=0):
    # Loop over each key, value pair in the dictionary
    for key, value in d.items():
        # Print the key with indentation based on its level in the nesting
        print(' ' * indent + f"{key}: ", end='')
        
        # Check if the value is another dictionary
        if isinstance(value, dict):
            print()  # Move to the next line
            # Recursive call to print nested dictionary with increased indentation
            print_nested_dict(value, indent + 4)
        else:
            # If the value is not a dictionary, just print it
            print(value)

def main():
    # Ensure exactly one command-line argument is provided
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <file.cl-ast>")
        sys.exit(1)

    inputFilename = sys.argv[1]
    if not inputFilename.endswith('.cl-ast'):
        print("ERROR: Input file must have a .cl-ast extension")
        sys.exit(1)

    try:
        # Initialize components
        reader = ASTReader(inputFilename)
        ast = reader.readAst()
        # printAST(ast)
        classTable = ClassTable()
        classTable.completeClassTable(ast)
        # print_nested_dict(classTable.data)
        # print("________________________")

        formatter = ASTFormatter()

        # Perform semantic analysis
        analyzer = SemanticAnalyzer(ast, classTable, formatter)
        analyzer.analyze()
        

        # Serialize output to .cl-type file
        outputFilename = inputFilename.replace('.cl-ast', '.cl-type')
        with open(outputFilename, 'w') as f:
            # Write Class Map
            classMap = classTable.classMap(formatter)
            f.write(classMap + "\n")
            
            
            # Write Implementation Map
            implementationMap = classTable.implementationMap(formatter)
            f.write(implementationMap + "\n")
            
            # Write Parent Map
            parentMap = classTable.parentMap()
            f.write(parentMap + "\n")
            

            # Write Annotated AST
            annotatedAst = formatter.formatProgram(ast)
            f.write(annotatedAst)

        # print(f"Semantic analysis completed successfully. Output written to {outputFilename}")

    except FileNotFoundError:
        print(f"ERROR: File {inputFilename} not found")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
