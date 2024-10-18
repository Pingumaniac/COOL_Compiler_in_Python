# type_checker.py

from symbol_table import SymbolTable
from class_table import ClassTable
from formatter import ASTFormatter
from ast_nodes import ExprNode, LetExpr, CaseExpr, LetBinding, AssignExpr, \
    DynamicDispatchExpr, StaticDispatchExpr, SelfDispatchExpr, IfExpr, \
    BlockExpr, SimpleExpr, LiteralExpr, UnaryExpr, BinaryExpr, WhileExpr, FormalNode
import sys

class TypeChecker:
    def report_error(self, line_number, message):
        print(f"ERROR: {line_number}: Type-Check: {message}")
        sys.exit(1)

    def __init__(self, classTable: ClassTable, formatter: ASTFormatter, symbolTable: SymbolTable):
        self.classTable = classTable
        self.formatter = formatter
        self.symbolTable = SymbolTable()

    def compatible(self, dest, source):
        while source != dest and source != "Object":
            source = self.classTable.getParent(source)
            if source == None:
                return False
        return source == dest

    def findSharedType(self, type1, type2):
        # Find the least common ancestor (shared type) of type1 and type2
        ancestors1 = self.getAncestors(type1)
        ancestors2 = self.getAncestors(type2)
        shared = set(ancestors1).intersection(set(ancestors2))
        if not shared:
            return "Object"
        # Return the closest ancestor
        for ancestor in ancestors1:
            if ancestor in shared:
                return ancestor
        return "Object"

    def getAncestors(self, typeName):
        ancestors = []
        while typeName:
            ancestors.append(typeName)
            typeName = self.classTable.getParent(typeName)
        return ancestors


    def checkLetVarTypes(self, expr: ExprNode,self_typee):
        if not expr:
            return
        if isinstance(expr, AssignExpr):
            self.checkLetVarTypes(expr.rhs, self_typee)
        elif isinstance(expr, (DynamicDispatchExpr, StaticDispatchExpr, SelfDispatchExpr)):
            self.checkLetVarTypes(expr.exp if isinstance(expr, (DynamicDispatchExpr, StaticDispatchExpr)) else None, self_typee)
            for arg in expr.args:
                self.checkLetVarTypes(arg, self_typee)
        elif isinstance(expr, IfExpr):
            self.checkLetVarTypes(expr.predicate, self_typee)
            self.checkLetVarTypes(expr.thenExpr, self_typee)
            self.checkLetVarTypes(expr.elseExpr, self_typee)
        elif isinstance(expr, BlockExpr):
            for e in expr.body:
                self.checkLetVarTypes(e, self_typee)
        elif isinstance(expr, (UnaryExpr, SimpleExpr, LiteralExpr)):
            if isinstance(expr, UnaryExpr):
                self.checkLetVarTypes(expr.expr, self_typee)
            if isinstance(expr, SimpleExpr):
                if expr.tag == "identifier":
                    name = expr.name[1]
                    line = expr.name[0]
                    bounded = False
                    for data_element in self.symbolTable.class_data:
                        if name == data_element[0]:
                            bounded = True
                    for scope in self.symbolTable.scope_data:
                        for data_element in scope:
                            if name == data_element[0]:
                                bounded = True
                    if not bounded and name != 'self':
                        self.report_error(line,f"Unbounded identifier {name}")

        elif isinstance(expr, BinaryExpr):
            self.checkLetVarTypes(expr.expr1, self_typee)
            self.checkLetVarTypes(expr.expr2, self_typee)
        elif isinstance(expr, LetExpr):
            new_scope = []
            for binding in expr.bindings:
                name = binding.var[1]
                typeName = binding.type[1]

                if typeName == 'SELF_TYPE':
                    if not isinstance(binding.expr, SimpleExpr):
                        self.report_error(binding.type[0] ,"Assigning not self to SELF_TYPE")
                    if binding.expr.name[1] != 'self' and binding.expr.name[1] != 'SELF_TYPE':
                        self.report_error(binding.type[0] ,"Assigning not self to SELF_TYPE")
                    new_scope.append((name, self_typee))
                else:
                    if not self.classTable.getClass(typeName):
                        self.report_error(binding.type[0] ,"No such type")
                    for (n, t) in new_scope:
                        if n == name:
                            self.report_error(binding.name[0],"Redeclared variable")
                    new_scope.append((name, typeName))
 
                if binding.expr:
                    self.checkLetVarTypes(binding.expr, self_typee)
            self.symbolTable.enter_scope(new_scope)
            self.checkLetVarTypes(expr.body, self_typee)
            self.symbolTable.exit_scope()

        elif isinstance(expr, CaseExpr):
            self.checkLetVarTypes(expr.expr, self_typee)
            for element in expr.elementsList:
                name = element.var[1]
                typeName = element.type[1]
                self.symbolTable.enter_scope([(name, typeName)])
                self.checkLetVarTypes(element.body, self_typee)
                self.symbolTable.exit_scope()
        elif isinstance(expr, WhileExpr):
            self.checkLetVarTypes(expr.predicate, self_typee)
            self.checkLetVarTypes(expr.body, self_typee)
        else:
            self.report_error(0, "Unrecognized expression")

    def annotateExpr(self, expr: ExprNode, self_typee):
        if not expr:
            return ""
        if isinstance(expr, AssignExpr):
            if expr.var[1] == 'self':
                self.report_error(expr.var[0], f"cannot assign to self")
            idType = self.symbolTable.findSymbol(expr.var[1])
            if not idType:
                self.report_error(expr.var[0], f"Variable {expr.var[1]} not declared")
            exprType = self.annotateExpr(expr.rhs, self_typee)

            destination = idType[1]
            if destination == "SELF_TYPE":
                destination = self_typee
            if not self.compatible(destination, exprType):
                self.report_error(expr.line,f"Can't assign {exprType} to {destination}")

            expr.annotatedType = expr.rhs.annotatedType
            return expr.annotatedType

        elif isinstance(expr, DynamicDispatchExpr):
            expr_type = self.annotateExpr(expr.exp, self_typee)
            arg_types = []
            for arg in expr.args:
                arg_types.append(self.annotateExpr(arg, self_typee)) 

            returnType = None

            for m in self.classTable.data[expr_type]['methods']:
                if m[0] == expr.method[1]:
                    destination_formals = m[1]
                    returnType = m[2][1]
            
            if not returnType:
                self.report_error(expr.line, "No matching function found")
            
            destination_types = []
            for destination_formal in destination_formals:
                if isinstance(destination_formal, FormalNode):
                    destination_types.append(destination_formal.arg_type)
                else:
                    destination_types.append(destination_formal[1]) 
            
            if len(arg_types) != len(destination_types):
                self.report_error(expr.line, "Incorrect number of arguments for dispatch")

            for i in range(len(arg_types)):
                if arg_types[i] == "SELF_TYPE":
                    t = self_typee
                else:
                    t = arg_types[i]
                if not self.compatible(destination_types[i], t):
                    self.report_error(expr.line, "dispatch parameters are not compatible")

            if returnType == 'SELF_TYPE':
                returnType = expr_type

            expr.annotatedType = returnType
            return expr.annotatedType


        elif isinstance(expr, StaticDispatchExpr):
            expType = self.annotateExpr(expr.exp, self_typee)
            dispatchType = expr.type[1]

            if expType == 'SELF_TYPE':
                expType = self_typee


            if not self.compatible(dispatchType, expType):
                self.report_error(expr.line, "Incompatible type in static dispatch")

            method = self.classTable.findMethod(dispatchType, expr.method[1])
            if not method:
                self.report_error(expr.line, "Unknown method")
            returnType = method[2][1]
            
            arg_types = []
            for arg in expr.args:
                self.annotateExpr(arg, dispatchType)
                arg_types.append(arg.annotatedType)

            destination_types = []
            for formal in method[1]:
                destination_types.append(formal.arg_type)

            if len(arg_types) != len(destination_types):
                self.report_error(expr.line, "Incorrect number of arguments for dispatch")
            

            for i in range(len(arg_types)):
                if arg_types[i] == "SELF_TYPE":
                    t = self_typee
                else:
                    t = arg_types[i]
                if not self.compatible(destination_types[i], t):
                    self.report_error(expr.line, "dispatch parameters are not compatible")

            expr.annotatedType = returnType
            return expr.annotatedType

        elif isinstance(expr, SelfDispatchExpr):
            arg_types = []
            for arg in expr.args:
                arg_types.append(self.annotateExpr(arg, self_typee)) 

            returnType = None
            destination_formal = None
            
            for m in self.classTable.data[self_typee]['methods']:
                if m[0] == expr.method[1]:
                    destination_formals = m[1]
                    returnType = m[2][1]
                    
            if not returnType:
                self.report_error(expr.line, "Self Dispatch method not found")
            
            destination_types = []

            for destination_formal in destination_formals:
                if isinstance(destination_formal, FormalNode):
                    destination_types.append(destination_formal.arg_type)
                else:
                    destination_types.append(destination_formal[1])
            
            if len(arg_types) != len(destination_types):
                self.report_error(expr.line, "Incorrect number of arguments for dispatch")
            

            for i in range(len(arg_types)):
                if arg_types[i] == "SELF_TYPE":
                    t = self_typee
                else:
                    t = arg_types[i]
                if not self.compatible(destination_types[i], t):
                    self.report_error(expr.line, "dispatch parameters are not compatible")
        
            expr.annotatedType = returnType
            
            return expr.annotatedType
        
        elif isinstance(expr, IfExpr):
            condType = self.annotateExpr(expr.predicate, self_typee)
            if condType != "Bool":
                self.report_error(expr.line, " Predicate in if statement must be Bool")
            thenType = self.annotateExpr(expr.thenExpr, self_typee)
            elseType = self.annotateExpr(expr.elseExpr, self_typee)
            
            if thenType == elseType:
                expr.annotatedType = thenType
            else:
                sharedType = self.findSharedType(thenType, elseType)
                expr.annotatedType = sharedType
            return expr.annotatedType

        elif isinstance(expr, BlockExpr):
            for e in expr.body[:-1]:
                self.annotateExpr(e, self_typee)
            last_expr_type = self.annotateExpr(expr.body[-1], self_typee)
            annotated_types = []
            for e in expr.body:
                annotated_types.append(e.annotatedType)
            shared_annotated_type = annotated_types[0]
            for i in range(len(annotated_types)):
                if i != 0:
                    shared_annotated_type = self.findSharedType(shared_annotated_type, annotated_types[i])
            expr.annotatedType = expr.body[-1].annotatedType
            expr.sharedType = shared_annotated_type
            return last_expr_type

        elif isinstance(expr, SimpleExpr):
            if expr.name[1] == 'self':
                expr.annotatedType = "SELF_TYPE"
                return self_typee
            if expr.tag == 'new':
                expr.annotatedType = expr.name[1]
                return expr.annotatedType

            var = self.symbolTable.retrieve_identifier_type(expr.name[1])
            if not var:
                self.report_error(expr.line, f"Variable {expr.name[1]} not declared")
            expr.annotatedType = var
            return var

        elif isinstance(expr, LiteralExpr):
            
            if expr.tag == 'integer':
                expr.annotatedType = "Int"
            elif expr.tag == 'string':
                expr.annotatedType = "String"
            elif expr.tag in ['true', 'false']:
                expr.annotatedType = "Bool"
            else:
                expr.annotatedType = None
            return expr.annotatedType

        elif isinstance(expr, UnaryExpr):
            subType = self.annotateExpr(expr.expr, self_typee)
            if expr.tag in ['negate', 'isvoid']:
                expr.annotatedType = "Int" if expr.tag == 'negate' else "Bool"
            elif expr.tag == 'not':
                if subType != "Bool":
                    self.report_error(expr.line, "'not' operator requires Bool type")
                expr.annotatedType = "Bool"
            else:
                expr.annotatedType = None
            return expr.annotatedType

        elif isinstance(expr, BinaryExpr):
            leftType = self.annotateExpr(expr.expr1, self_typee)
            rightType = self.annotateExpr(expr.expr2, self_typee)

            if expr.tag in ['plus', 'minus', 'times', 'divide']:
                if leftType != "Int" or rightType != "Int":
                    self.report_error(expr.line, "Arithmetic operations require Int types")
                expr.annotatedType = "Int"
            elif expr.tag in ['lt', 'le']:
                if leftType == "Int" and rightType == "Int":
                    expr.annotatedType = "Bool"
                elif leftType =="String" and rightType =="String":
                    expr.annotatedType = "Bool"
                elif leftType =="Bool" and rightType =="Bool":
                    expr.annotatedType = "Bool"
                elif leftType not in ["String", "Bool", "Int"] and rightType not in ["String", "Bool", "Int"]:
                    expr.annotatedType = "Bool"
                else:
                    self.report_error(expr.line, "Comparison arguments not allowed")
                
            elif expr.tag == 'eq':
                staticList = ['String', 'Bool', 'Int']
                if (leftType in staticList or rightType in staticList) and (leftType != rightType):
                    self.report_error(expr.line, "Types must match for equality with static types")
                expr.annotatedType = "Bool"
            elif expr.tag == 'while':
                if leftType != "Bool":
                    self.report_error(expr.line, "'while' predicate must be Bool")
                expr.annotatedType = rightType
            else:
                expr.annotatedType = None
            return expr.annotatedType

        elif isinstance(expr, LetExpr):
            new_scope = []
            for binding in expr.bindings:
                name = binding.var[1]
                typeName = binding.type[1]

                if typeName == 'SELF_TYPE':
                    if not isinstance(binding.expr, SimpleExpr):
                        self.report_error(binding.type[0] ,"Assigning not self to SELF_TYPE")
                    if binding.expr.name[1] != 'self' and binding.expr.name[1] != 'SELF_TYPE':
                        self.report_error(binding.type[0] ,"Assigning not self to SELF_TYPE")
                    new_scope.append((name, 'SELF_TYPE'))
                else:
                    if name == 'self':
                        self.report_error(expr.line, "can't bind self in a let binding")
                    if not self.classTable.getClass(typeName):
                        self.report_error(expr.line, "Undefined type in let binding")
                    for (n, t) in new_scope:
                        if n == name:
                            self.report_error(expr.line, "Redeclared variable")
                    if binding.expr:
                        bodyType = self.annotateExpr(binding.expr,self_typee)
                        if not self.compatible(typeName, bodyType):
                            self.report_error(expr.line,"initializer types in let binding does not conform")   
                    new_scope.append((name, typeName))
                
                if binding.expr:
                    self.annotateExpr(binding.expr, self_typee)
            self.symbolTable.enter_scope(new_scope)

            exprType = self.annotateExpr(expr.body, self_typee)
            
            if isinstance(expr.body, BlockExpr):
                # expr.annotatedType = expr.body.sharedType
                expr.annotatedType = expr.body.annotatedType
            elif isinstance(expr.body, WhileExpr):
                expr.annotatedType = expr.body.annotatedType
            elif isinstance(expr.body, LetExpr):
                expr.annotatedType = expr.body.annotatedType
            else:
                expr.annotatedType = exprType
            self.symbolTable.exit_scope()
        
            # return expr.body.annotatedType
            if expr.body.annotatedType == "SELF_TYPE" or exprType == "SELF_TYPE":
                expr.body.annotatedType = "SELF_TYPE"
                return "SELF_TYPE"
            return exprType
        
        elif isinstance(expr, CaseExpr):
            exprType = self.annotateExpr(expr.expr, self_typee)
            resultType = None
            case_list = []
            for element in expr.elementsList:
                if element.type[1] == 'SELF_TYPE':
                    self.report_error(element.type[0], "SELF_TYPE cannot be a case branch")
                if element.type[1] not in self.symbolTable.types:
                    self.report_error(element.type[0], "Undefined type in case element")
                scope_element = [(element.var[1], element.type[1])]
                self.symbolTable.enter_scope(scope_element)
                elementType = self.annotateExpr(element.body, self_typee)
                if element.type[1] in case_list:
                    self.report_error(element.type[0], f"case branch type {elementType} is bound twice")
                else:
                    case_list.append(element.type[1])
                if resultType is None:
                    resultType = elementType
                else:
                    resultType = self.findSharedType(resultType, elementType)
                self.symbolTable.exit_scope()
            expr.annotatedType = resultType
            
            return expr.annotatedType
        elif isinstance(expr, WhileExpr):
            condType = self.annotateExpr(expr.predicate, self_typee)
            if condType != "Bool":
                self.report_error(expr.line, "Predicate in if statement must be Bool")
            bodyType = self.annotateExpr(expr.body, self_typee)
            # if isinstance(expr.body, BlockExpr):
            #     expr.annotatedType = expr.body.sharedType
            # else:
            #     expr.annotatedType = bodyType
            expr.annotatedType = "Object"
            return bodyType

            # bodyType = self.annotateExpr(expr.body, self_typee)
            # expr.annotatedType = bodyType
            # return expr.annotatedType
        else:
            self.report_error(0, "Unrecognized expression")

       
