# ast_reader.py

from ast_nodes import (
    ClassNode, MethodFeature, FormalNode, AttributeInitFeature,
    AttributeNoInitFeature, AssignExpr, DynamicDispatchExpr,
    StaticDispatchExpr, SelfDispatchExpr, IfExpr, WhileExpr, BlockExpr,
    SimpleExpr, LiteralExpr, UnaryExpr, BinaryExpr, LetExpr, CaseExpr,
    LetBinding, CaseElement
)

class ASTReader:
    def __init__(self, filename, debug=False):
        self.filename = filename
        self.file = open(filename, 'r')
        self.debug = debug  # Toggle debugging output

    def debug_print(self, message):
        if self.debug:
            print(message)

    def readAst(self):
        self.debug_print("Reading AST from file.")
        programClassList = self.getList(self.getClass)
        self.file.close()
        return programClassList

    def getLine(self):
        line = self.file.readline().rstrip("\n\r")
        self.debug_print(f"Line read: {line}")
        return line

    def getList(self, getFunction):
        count = int(self.getLine())
        self.debug_print(f"Expecting {count} elements in list.")
        return [getFunction() for _ in range(count)]

    def getId(self):
        line = self.getLine()
        id = self.getLine()
        self.debug_print(f"ID: (line={line}, id={id})")
        return (line, id)

    def getFormal(self):
        arg_name_lino = self.getLine()
        arg_name = self.getLine()
        arg_type_lino = self.getLine()
        arg_type = self.getLine()
        self.debug_print(f"Formal: name={arg_name}, type={arg_type}")
        return FormalNode(arg_name_lino, arg_name, arg_type_lino, arg_type)

    def getExpr(self):
        lino = self.getLine()
        tag = self.getLine()
        self.debug_print(f"Expression tag: {tag}")

        if tag == 'assign':
            var = self.getId()
            rhs = self.getExpr()
            return AssignExpr(lino, tag, var, rhs)
        elif tag == 'dynamic_dispatch':
            exp = self.getExpr()
            method = self.getId()
            args = self.getList(self.getExpr)
            return DynamicDispatchExpr(lino, tag, exp, method, args)
        elif tag == 'static_dispatch':
            exp = self.getExpr()
            type = self.getId()
            method = self.getId()
            args = self.getList(self.getExpr)
            return StaticDispatchExpr(lino, tag, exp, type, method, args)
        elif tag == 'self_dispatch':
            method = self.getId()
            args = self.getList(self.getExpr)
            return SelfDispatchExpr(lino, tag, method, args)
        elif tag == 'if':
            predicate = self.getExpr()
            thenExpr = self.getExpr()
            elseExpr = self.getExpr()
            return IfExpr(lino, tag, predicate, thenExpr, elseExpr)
        elif tag == 'while':
            predicate = self.getExpr()
            body = self.getExpr()
            return WhileExpr(lino, tag, predicate, body)
        elif tag == 'block':
            body = self.getList(self.getExpr)
            return BlockExpr(lino, tag, body)
        elif tag in ['new', 'identifier']:
            name = self.getId()
            return SimpleExpr(lino, tag, name)
        elif tag in ['integer', 'string']:
            value = self.getLine()
            return LiteralExpr(lino, tag, value)
        elif tag in ['true', 'false']:
            return LiteralExpr(lino, tag)
        elif tag in ['negate', 'not', 'isvoid']:
            expr = self.getExpr()
            return UnaryExpr(lino, tag, expr)
        elif tag in ['plus', 'minus', 'times', 'divide', 'lt', 'le', 'eq']:
            expr1 = self.getExpr()
            expr2 = self.getExpr()
            return BinaryExpr(lino, tag, expr1, expr2)
        elif tag == 'let':
            bindings = self.getList(self.getLetBinding)
            body = self.getExpr()
            return LetExpr(lino, tag, bindings, body)
        elif tag == 'case':
            expr = self.getExpr()
            elementsList = self.getList(self.getCaseElement)
            return CaseExpr(lino, tag, expr, elementsList)
        else:
            raise ValueError(f'Unrecognized expression: {lino} {tag}')

    def getLetBinding(self):
        bind = self.getLine()
        var = self.getId()
        type = self.getId()
        expr = self.getExpr() if bind == 'let_binding_init' else None
        self.debug_print(f"Let binding: var={var[1]}, type={type[1]}")
        return LetBinding(bind, var, type, expr)

    def getCaseElement(self):
        var = self.getId()
        type = self.getId()
        body = self.getExpr()
        self.debug_print(f"Case element: var={var[1]}, type={type[1]}")
        return CaseElement(var, type, body)

    def getFeature(self):
        feature_type = self.getLine()
        self.debug_print(f"Feature type: {feature_type}")

        if feature_type == 'attribute_no_init':
            attribute_name_lino = self.getLine()
            attribute_name = self.getLine()
            attribute_type_lino = self.getLine()
            attribute_type = self.getLine()
            return AttributeNoInitFeature(attribute_name_lino, attribute_name, attribute_type_lino, attribute_type)
        elif feature_type == 'attribute_init':
            attribute_name_lino = self.getLine()
            attribute_name = self.getLine()
            attribute_type_lino = self.getLine()
            attribute_type = self.getLine()
            init_expr = self.getExpr()
            return AttributeInitFeature(attribute_name_lino, attribute_name, attribute_type_lino, attribute_type, init_expr)
        elif feature_type == 'method':
            method_name_lino = self.getLine()
            method_name = self.getLine()
            formalsList = self.getList(self.getFormal)
            return_type_lino = self.getLine()
            return_type = self.getLine()
            body = self.getExpr()
            return MethodFeature(method_name_lino, method_name, formalsList, return_type, return_type_lino, body)
        else:
            raise ValueError(f'Unrecognized feature: {feature_type}')

    def getClass(self):
        lino = self.getLine()
        class_name = self.getLine()
        inherits = self.getLine()

        if inherits == 'inherits':
            parent_type_lino = self.getLine()
            parent_type = self.getLine()
        else:
            parent_type_lino = -1
            parent_type = "Object"

        self.debug_print(f"Class: {class_name}, inherits from {parent_type}")
        featureList = self.getList(self.getFeature)
        return ClassNode(class_name, lino, inherits, parent_type, parent_type_lino, featureList)